from app import db

db.Model.metadata.reflect(db.engine)

class Shapefiles(db.Model):
    __table__ = db.Model.metadata.tables['Shapefiles']
    __table_args__ = {'extend_existing': True}
