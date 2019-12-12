import tempfile
import pickle
import shutil
from io import BytesIO
import uuid
from functools import reduce
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from flask import render_template, Response, request, redirect, url_for, send_file, flash, session, g
from app import app, forms
from app.models import Shapefiles

def csv_to_gdf(file, proj):
    '''
    Takes a CSV with latitude and longitude columns
    and converts it to a GeoDataFrame
    '''
    df = pd.read_csv(file, delimiter=",")
    geometry = [Point(xy) for xy in zip(df.Lon, df.Lat)]
    if proj == 'wgs':
        crs = {'init': 'epsg:4326'}
    if proj == 'stateplane':
        crs = {'init': 'epsg:2263'}
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
#
# def make_result_map(gdf):
#     folium_map = folium.Map(
#         location=[gdf['lat'].mean(), gdf['lon'].mean()],
#         tiles='CartoDB positron',
#         zoom_start=10,
#         width='75%',
#         height='75%'
#     )
#     callback = ('function (row) {'
#                 'var circle = L.circle(new L.LatLng(row[0], row[1]), {color: "red",  radius: 10000});'
#                 'return circle};')
#     folium_map.add_child(FastMarkerCluster(gdf[['lat', 'lon']].values.tolist()))
#     folium_map.save('app/templates/complete_map.html')
#     # return folium_map.to_json()

def df_2_geojson(df, properties, proj):
    '''
    Turn a dataframe containing point data into a geojson formatted python dictionary
    '''

    if proj == 'stateplane':
        df = df.to_crs(epsg='4326')
        df = df.assign(lat2=df.geometry.y)
        df = df.assign(lon2=df.geometry.x)
        lat = 'lat2'
        lon = 'lon2'
    else:
        df = df
        lat = 'lat'
        lon = 'lon'

    # create a new python dict to contain our geojson data, using geojson format
    geojson = {'type': 'FeatureCollection', 'features': []}

    # loop through each row in the dataframe and convert each row to geojson format
    for _, row in df.iterrows():
        # create a feature template to fill in
        feature = {"type": "Feature",
                   "properties": {},
                   "geometry": {"type": "Point",
                                "coordinates": []}}

        # fill in the coordinates
        feature["geometry"]["coordinates"] = [row[lon], row[lat]]

        # for each column, get the value and add it as a new feature property
        for prop in properties:
            feature["properties"][prop] = row[prop]

        # add this feature (aka, converted dataframe row) to the list of features inside our dict
        geojson["features"].append(feature)

    return geojson


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
        org = csv_to_gdf(lines, proj)
        org_cols = list(org.columns)
        org_cols.remove('geometry')
        org_cols = [name.lower() for name in org_cols]
        new_cols = org_cols + join_cols

        input_frames = [gpd.read_file(path) for path in shp_paths]
        new_input_frames = []
        for gdf in input_frames:
            gdf = gdf.to_crs(org.crs)
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
        sjoin = sjoin.loc[:, ~sjoin.columns.duplicated()]
        sjoin2 = sjoin[new_cols]
        result = df_2_geojson(sjoin, properties=new_cols, proj=proj)
        # make_result_map(sjoin)
        # result = pd.DataFrame(sjoin).to_csv(index=False, encoding='utf-8')

        result_id = uuid.uuid4()
        result_dict = {str(result_id) : sjoin2.to_json(orient='split')}
        session['tempdir'] = tempfile.mkdtemp()
        outfile = open(session['tempdir'] + '/filename', 'wb')
        pickle.dump(result_dict, outfile)
        outfile.close()

        return render_template('success.html', result_id=list(result_dict)[0], result=result)

        # return Response(result, mimetype="text/csv",
        #                 headers={"Content-disposition": "attachment; filename=output.csv"})
    else:
        return render_template('form.html', form=form)

# @app.route('/make_map/<gdf>')
# def make_map(sjoin):
#     if request.method == 'GET':
#         make_result_map(sjoin)

@app.route('/download_file/<result_id>')
def download_file(result_id):
    if request.method == 'GET':
        infile = open(session['tempdir'] + '/filename', 'rb')
        result_dict = pickle.load(infile)
        infile.close()
        output = pd.read_json(result_dict[result_id], orient='split').to_csv(index=False, encoding='utf-8')
        shutil.rmtree(session['tempdir'])
        session.pop('tempdir', None)
        return Response(output, mimetype="text/csv",
                        headers={"Content-disposition": "attachment; filename=output.csv"})

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def something_wrong(error):
    return render_template('500.html'), 500