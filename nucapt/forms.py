from wtforms import Form, StringField, TextAreaField, FieldList, FormField, RadioField, FloatField, DecimalField
from wtforms.fields.simple import FileField
from wtforms.validators import NumberRange, Regexp, Optional


class KeyValueForm(Form):
    key = StringField('Key')
    value = StringField('Value')


class AuthorForm(Form):
    """Form to describe author information"""
    first_name = StringField('First Name', description='Given Name')
    last_name = StringField('Last Name', description='Family Name')
    affiliation = StringField('Affiliation', description='Name of home institution')


class DatasetForm(Form):
    """Form for creating a new dataset"""
    title = StringField('Title')
    abstract = TextAreaField('Abstract', description='Abstract describing this experiment. As long as necessary')
    authors = FieldList(FormField(AuthorForm), 'Authors',
                        min_entries=1,
                        description='People associated with this dataset')


class APTCollectionMethodForm(Form):
    """Form to capture leap metadata

    LW 13Jul17: We should select real default values to these"""

    leap_model = StringField('LEAP Model', description="Model of LEAP used to collect data",
                             default='4000 Si X')
    evaporation_mode = RadioField('Evaporation Mode', choices=[('voltage', 'Voltage'), ('laser', 'Laser')],
                                  description='Method used to evaporate sample',
                                  default='voltage')
    voltage_ratio = FloatField('Voltage Ratio', description='Voltage ratio used in evaporation',
                               validators=[NumberRange(min=0, message='Voltage ratio must be positive')],
                               default=1)
    laser_pulse_energy = FloatField('Laser Pulse Energy', description='Laser pulse energy used in evaporation (pJ)',
                                    validators=[NumberRange(min=0, message='Energy must be positive')],
                                    default=1)
    laser_frequency = FloatField('Laser Frequency', description='Laser frequency (kHz)',
                                 validators=[NumberRange(min=0, message='Frequency must be positive')],
                                 default=1)
    temperature = FloatField('Temperature', description='Temperature (K)', default=1)
    detection_rate = FloatField('Detection Rate', description='Detection rate (ions/pulse)', default=1)
    starting_voltage = FloatField('Starting Voltage', description='Starting voltage (kV)', default=1)
    chamber_pressure = FloatField('Chamber Vacuum Pressure', description='Chamber pressure (torr)', default=1)
    misc = FieldList(FormField(KeyValueForm), 'Other Metadata', description='Anything else that is pertinent')


class APTSampleElectropolishingForm(Form):
    """Form for an electropolishing step"""

    solution = StringField('Solution', description='Electropolishing solution', validators=[Optional()])
    voltage = FloatField('Voltage', description='Electropolishing voltage (V)', validators=[Optional()])
    temperature = FloatField('Temperature', description='Electropolishing temperature (C)', validators=[Optional()])
    electrode_shape = StringField('Electrode Shape', description='Shape of electrode', validators=[Optional()])


class APTFIBLiftoutStepForm(Form):
    """Form for liftout_step"""

    capping_material = StringField('Capping Material', description='Capping material', validators=[Optional()])
    wedge_dimension = FloatField('Wedge Dimension', description='Wedge dimension (m)', validators=[Optional()])
    ion_voltage = FloatField('Ion Voltage', description='Ion voltage (kV)', validators=[Optional()])
    ion_current = FloatField('Ion Current', description='Ion current (nA)', validators=[Optional()])
    sample_orientation = StringField('Sample Orientation', description='Sample orientation', validators=[Optional()])


class APTSharpeningStepForm(Form):
    """For for the sharpening step"""

    final_ion_voltage = FloatField('Final Ion Voltage', description='Final ion voltage (kV)', validators=[Optional()])
    final_ion_current = FloatField('Final Ion Current', description='Final ion current (pA)', validators=[Optional()])


class APTFIBPreparationForm(Form):
    """Form for describing FIB liftout"""

    lift_out_step = FormField(APTFIBLiftoutStepForm, 'Lift Out Step', description='Lift out step metadata')
    sharpening_step = FormField(APTSharpeningStepForm, 'Sharpening Step', description='Sharpening step metadata')


class APTSamplePreparationForm(Form):
    """Description of how an APT sample was prepared"""

    preparation_method = RadioField('Preparation Method', description='Method used to create sample',
                                    choices=[('electropolish', 'Electropolishing'), ('fib_lift_out', 'FIB Lift Out')],
                                    default='electropolish')
    electropolish = FieldList(FormField(APTSampleElectropolishingForm), 'Electropolishing',
                              description='Electropolishing step', min_entries=1)
    fib_lift_out = FormField(APTFIBPreparationForm, 'FIB liftout metadata')


class APTSampleDescriptionForm(Form):
    """Description of a LEAP sample"""

    sample_title = StringField('Sample Title', description='Short description of sample')
    sample_description = TextAreaField('Sample Description', description='Longer-form description of the sample')
    metadata = FieldList(FormField(KeyValueForm), 'Sample Metadata',
                         description='Structured metadata about sample. Use to make indexing easier')


class APTSampleForm(Form):
    """Form to get data for a new sample"""

    sample_name = StringField('Sample Name', description='Name of sample directory. Cannot contain whitespace.',
                              render_kw=dict(pattern='\\w+',
                                             title='Only word characters allowed: A-Z, a-z, 0-9, and _'),
                              validators=[Regexp('\\w+', message='File name can only contain word '
                                                                 'characters: A-Z, a-z, 0-9, and _')])
    sample_form = FormField(APTSampleDescriptionForm, description="Metadata for the ")
    collection_form = FormField(APTCollectionMethodForm, description="Metadata for data collection method")
    preparation_form = FormField(APTSamplePreparationForm, description="Metadata for sample preparation")
    rhit_file = FileField('RHIT file')


class APTReconstructionForm(Form):
    """Form to describe metadata for a APT reconstruction"""

    title = StringField('Title', description='Title for this reconstruction')
    description = TextAreaField('Description', description='Longer-form description of this reconstruction')
    reconstruction_method = RadioField('Reconstruction Method', description='Method used to reconstruct APT data',
                                       choices=[('shank_angle', 'Shank Angle'), ('voltage_profile', 'Voltage Profile'),
                                                ('tip_image', 'Tip Image')], default='shank_angle')
    tip_radius = FloatField('Initial Tip Radius', description='Initial tip radius (nm)', render_kw={'min': 0},
                              validators=[Optional()])
    shank_angle = FloatField('Shank Angle', description='Shank angle (degrees)', render_kw={'min': 0},
                               validators=[Optional()])
    tip_image = FileField('Tip Image', description='SEM image of tip')
    metadata = FieldList(FormField(KeyValueForm), 'Reconstruction Metadata',
                         description='Structured metadata about reconstruction. Use to make indexing easier')
    pos_file = FileField('POS File', render_kw={'accept': '.pos,.POS'})
    rrng_file = FileField('RRNG File', render_kw={'accept': '.rrng,.RRNG'})


class AddAPTReconstructionForm(APTReconstructionForm):
    """Form to add reconstruction metadata to a sample"""

    name = StringField('Name', description='Name of reconstruction',
                       render_kw=dict(pattern='\\w+', title='Only word characters allowed: A-Z, a-z, 0-9, and _'),
                       validators=[Regexp('\\w+', message='Reconstruction name can only contain word '
                                                          'characters: A-Z, a-z, 0-9, and _')])
