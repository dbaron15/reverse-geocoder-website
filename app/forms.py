from wtforms import SelectField, SelectMultipleField, SubmitField
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, DataRequired


class UploadForm(FlaskForm):
    """File upload and shapefile selection form"""

    upload = FileField('CSV File', validators=[FileRequired(), FileAllowed(['csv'], 'Invalid File Type. Must be .csv')])
    projection = SelectField('What projection is your data in?', validators=[DataRequired()], choices=[('wgs', 'Geographic'),
                                                                                                      ('stateplane', 'Long Island State Plane')])
    selection = SelectMultipleField('Geographies to Join On', validators=[DataRequired()], choices=[("uhf34", "UHF34"),
                                                                                                    ("uhf42", "UHF42"),
                                                                                                    ("zcta", "Zip Code Tabulation Areas"),
                                                                                                    ("precincts", "Police Precincts"),
                                                                                                    ("ccd", "City Council Districts"),
                                                                                                    ("uscong", "U.S. Congressional Districts"),
                                                                                                    ("schooldist", "School Districts"),
                                                                                                    ("file_uploads/nycd.shp", "Community Districts"),
                                                                                                    ("nta", "Neighborhood Tabulation Areas"),
                                                                                                    ("file_uploads/nyct2010.shp","2010 Census Tracks"),
                                                                                                    ("census_blocks", "2010 Census Blocks"),
                                                                                                    ("evaczone", "Hurricane Evacuation Zones")])
    submit = SubmitField("Process")