import os
from io import BytesIO
from functools import reduce
from glob import glob
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium.plugins import FastMarkerCluster
from flask import render_template, Response, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app, forms
from app.models import Shapefiles

def csv_to_gdf(file):
    '''
    Takes a CSV with latitude and longitude columns
    and converts it to a GeoDataFrame
    '''
    df = pd.read_csv(file, delimiter=",")
    geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
    crs = {'init': 'epsg:4326'}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
    return gdf

def get_paths_n_joincol(shps):
    '''
    Takes a list of shapefile names and matches them
    with their full system paths and join columns on the server
    '''
    paths = []
    join_cols = []
    for shp in shps:
        file = Shapefiles.query.filter_by(rowid=shp).first()
        paths.append(str(file.syspath))
        join_cols.append(str(file.join_column).lower())
        if file.join_column2 is not None:
            join_cols.append(str(file.join_column2).lower())
    return paths, join_cols

def sjoin_no_index(left, right):
    '''
    Takes two GeoDataFrames, do a spatial join, and return without the
    index_left and index_right columns.
    '''
    sjoin = gpd.sjoin(left, right, how='left', op='within')
    for column in ['index_left', 'index_right']:
        try:
            sjoin.drop(column, axis=1, inplace=True)
        except KeyError:
            pass
    return sjoin

def make_result_map(gdf):
    folium_map = folium.Map(
        location=[gdf['lat'].mean(), gdf['lon'].mean()],
        tiles='CartoDB positron',
        zoom_start=10,
        width='75%',
        height='75%'
    )
    callback = ('function (row) {'
                'var circle = L.circle(new L.LatLng(row[0], row[1]), {color: "red",  radius: 10000});'
                'return circle};')
    folium_map.add_child(FastMarkerCluster(gdf[['lat', 'lon']].values.tolist()))
    folium_map.save('app/templates/complete_map.html')
    # return folium_map.to_json()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/processing', methods=['GET', 'POST'])
def home():
    shp_choices = [(row.rowid, row.name) for row in Shapefiles.query.all()]
    form = forms.UploadForm()
    form.selection.choices = shp_choices
    if form.validate_on_submit():
        file = form.upload.data
        shp_list = form.selection.data
        proj = form.projection.data
        shp_paths, join_cols = get_paths_n_joincol(shp_list)
        f = file.stream.read()
        lines = BytesIO(f)
        org = csv_to_gdf(lines)
        org_cols = list(org.columns)
        org_cols.remove('geometry')
        org_cols = [name.lower() for name in org_cols]
        new_cols = org_cols + join_cols

        input_frames = [gpd.read_file(path) for path in shp_paths]
        if proj == 'wgs':
            new_input_frames = []
            for gdf in input_frames:
                gdf = gdf.to_crs(epsg=4326)
                new_input_frames.append(gdf)
            input_frames = new_input_frames
        input_frames.insert(0, org)
        sjoin = reduce(sjoin_no_index, input_frames)
        sjoin.columns = sjoin.columns.str.lower()
        for col in list(sjoin.columns):
            if col.endswith('_left'):
                sjoin.rename(columns={col : col[:-5]}, inplace=True)
            if col.endswith('_right'):
                sjoin.rename(columns={col : col[:-6]}, inplace=True)
            else:
                pass
        sjoin.drop('geometry', axis=1, inplace=True)
        sjoin = sjoin.loc[:, ~sjoin.columns.duplicated()]
        sjoin = sjoin[new_cols]
        make_result_map(sjoin)
        # result = pd.DataFrame(sjoin).to_csv(index=False, encoding='utf-8')
        flash('Please wait, your file is being processed and will download automatically when complete.')

        return render_template('success.html', sjoin=sjoin)

        # return Response(result, mimetype="text/csv",
        #                 headers={"Content-disposition": "attachment; filename=output.csv"})

    return render_template('form.html', form=form)

# @app.route('/make_map/<gdf>')
# def make_map(sjoin):
#     if request.method == 'GET':
#         make_result_map(sjoin)

@app.route('/download_file/<result>')
def download(sjoin):
    if request.method == 'GET':
        result = pd.DataFrame(sjoin).to_csv(index=False, encoding='utf-8')
        return Response(result, mimetype="text/csv",
                        headers={"Content-disposition": "attachment; filename=output.csv"})


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def something_wrong(error):
    return render_template('500.html'), 500