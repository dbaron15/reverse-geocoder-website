import os
basedir = os.path.abspath(os.path.dirname(__file__))


class DevelopmentConfig(object):

    UPLOAD_FOLDER = 'E:/code/dbaron/IntersectGeocoder/file_uploads'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///E://code//dbaron//IntersectGeocoder//app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 's0-s3cur3'

class ProductionConfig(object):
    UPLOAD_FOLDER = 'E:/code/dbaron/IntersectGeocoder/file_uploads'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///E://code//dbaron//IntersectGeocoder//app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "b'\x93>\xdc\x08g\xc6v\x9f\xf6\xf56\xa9\xf1j\xac\xe75\xf2\xfc\x85\xc0h\xb1>"