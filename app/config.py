import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    UPLOAD_FOLDER = 'E:/code/dbaron/IntersectGeocoder/file_uploads'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///E://code//dbaron//IntersectGeocoder//app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 's0-s3cur3'