import os
from io import BytesIO
from functools import reduce
from glob import glob
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from flask import render_template, Response, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from app import app, forms, config

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

def get_paths(shps):
    '''
    Takes a list of shapefile names and matches them
    with their full system paths on the server
    '''
    paths = []
    for shp in shps:
        file = glob(str(shp))
        paths.append(file[0])
    return paths

def sjoin_no_index(left, right):
    '''
    Takes two GeoDataFrames, do a spatial join, and return without the
    index_left and index_right columns.
    '''
    sjoin = gpd.sjoin(left, right, how='left')
    for column in ['index_left', 'index_right']:
        try:
            sjoin.drop(column, axis=1, inplace=True)
        except KeyError:
            pass
    return sjoin

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/processing', methods=['GET', 'POST'])
def home():
    form = forms.UploadForm()

    if form.validate_on_submit():
        file = form.upload.data
        shp_list = form.selection.data
        proj = form.projection.data
        shp_paths = get_paths(shp_list)
        f = file.stream.read()
        lines = BytesIO(f)
        org = csv_to_gdf(lines)

        input_frames = [gpd.read_file(path) for path in shp_paths]
        if proj == 'wgs':
            new_input_frames = []
            for gdf in input_frames:
                gdf = gdf.to_crs(epsg=4326)
                new_input_frames.append(gdf)
            input_frames = new_input_frames
        input_frames.insert(0, org)
        sjoin = reduce(sjoin_no_index, input_frames)
        sjoin.drop('geometry', axis=1, inplace=True)
        result = pd.DataFrame(sjoin).to_csv()

        return Response(result, mimetype="text/csv",
                        headers={"Content-disposition": "attachment; filename=output.csv"})
        #return render_template('success.html')

    return render_template('form.html', form=form)

    
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
@app.errorhandler(500)
def something_wrong(error):
    return render_template('500.html'), 500