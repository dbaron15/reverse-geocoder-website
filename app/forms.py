from wtforms import RadioField, SelectMultipleField, SubmitField, widgets
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, DataRequired

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class UploadForm(FlaskForm):
    """File upload and shapefile selection form"""

    upload = FileField('Choose Your CSV File', validators=[FileRequired(), FileAllowed(['csv'], 'Invalid File Type. Must be .csv')])
    projection = RadioField('What Projection is Your Data In?', validators=[DataRequired()], choices=[('wgs', 'Geographic'),
                                                                                                      ('stateplane', 'Long Island State Plane')])
    selection = MultiCheckboxField('Geographies to Join On', validators=[DataRequired()], coerce=int)
    submit = SubmitField("Process")