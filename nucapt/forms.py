from flask_wtf import Form
from wtforms import StringField, TextAreaField, FieldList, FormField, RadioField, FloatField
from wtforms.fields.simple import FileField
from wtforms.validators import NumberRange


class KeyValueForm(Form):
    key = StringField('Key')
    value = StringField('Value')


class AuthorForm(Form):
    """Form to describe author information"""
    first_name = StringField('First Name', description='Given Name')
    last_name = StringField('Last Name', description='Family Name')
    affiliation = StringField('Affiliation', description='Name of home institution')


class CreateForm(Form):
    """Form for creating a new dataset"""
    title = StringField('Title')
    abstract = TextAreaField('Abstract', description='Abstract describing this experiment. As long as necessary')
    authors = FieldList(FormField(AuthorForm), 'Authors',
                        min_entries=1,
                        description='People associated with this dataset')


class LEAPMetadataForm(Form):
    """Form to capture leap metadata

    LW 13Jul17: We should select real default values to these"""

    leap_model = StringField('LEAP Model', description="Model of LEAP used to collect data",
                             default='A nice one')
    evaporation_mode = RadioField('Evaporation Mode', choices=[('voltage','Voltage'), ('laser','Laser')],
                                  description='Method used to evaporate sample',
                                  default='v')
    voltage_ratio = FloatField('Voltage Ratio', description='Voltage ratio used in evaporation (units)',
                               validators=[NumberRange(min=0, message='Voltage ratio must be positive')],
                               default=1)
    laser_pulse_energy = FloatField('Laser Pulse Energy', description='Laser pulse energy used in evaporation (units)',
                                    validators=[NumberRange(min=0, message='Energy must be positive')],
                                    default=1)
    laser_frequency = FloatField('Laser Frequency', description='Laser frequency (units)',
                                 validators=[NumberRange(min=0, message='Frequency must be positive')],
                                 default=1)
    temperature = FloatField('Temperature', description='Temperature (units)', default=1)
    detection_rate = FloatField('Detection Rate', description='Detection rate (ions/pulse)', default=1)
    starting_voltage = FloatField('Starting Voltage', description='Starting voltage (units)', default=1)
    chamber_pressure = FloatField('Chamber Vacuum Pressure', description='Chamber pressure (torr)', default=1)
    misc = FieldList(FormField(KeyValueForm), 'Other Metadata', description='Anything else that is pertinent')


class LEAPSampleDescriptionForm(Form):
    """Description of a LEAP sample"""

    sample_name = StringField('Sample Name', description='Name for sample')
    sample_description = TextAreaField('Sample Description', description='Longer-form description of the sample')
    metadata = FieldList(FormField(KeyValueForm), 'Sample Metadata',
                         description='Structured metadata about materials. Use to make indexing easier')


class LEAPRawDataForm(Form):
    """Form to collect raw data files"""

    rhit_file = FileField('RHIT file')
    rrng_file = FileField('RRNG file')


class LEAPSampleForm(Form):
    """Form to get data for a new sample"""

    sample_form = FormField(LEAPSampleDescriptionForm, description="Metadata for the ")
    collection_form = FormField(LEAPMetadataForm, description="Metadata for data collection method")
    file_form = FormField(LEAPRawDataForm, description="Raw data files")