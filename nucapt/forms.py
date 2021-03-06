from datetime import date
from collections import OrderedDict

from wtforms import Form, StringField, TextAreaField, FieldList, FormField, RadioField, FloatField, BooleanField
from wtforms.fields.simple import FileField
from wtforms.fields.html5 import EmailField
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
    # TODO: Add MRR-related fields to data file


class APTCollectionMethodForm(Form):
    """Form to capture leap metadata

    LW 13Jul17: We should select real default values to these"""

    leap_model = StringField('LEAP Model', description="Model of LEAP used to collect data",
                             default='4000 Si X')
    evaporation_mode = RadioField('Evaporation Mode', choices=[('voltage', 'Voltage'), ('laser', 'Laser')],
                                  description='Method used to evaporate sample',
                                  default='laser')
    voltage_ratio = FloatField('Voltage Ratio', description='Voltage ratio used in evaporation',
                               validators=[Optional(), NumberRange(min=0, message='Voltage ratio must be positive')],
                               default=1)
    laser_pulse_energy = FloatField('Laser Pulse Energy', description='Laser pulse energy used in evaporation (pJ)',
                                    validators=[Optional(), NumberRange(min=0, message='Energy must be positive')])
    laser_pulse_frequency = FloatField('Laser Pulse Frequency', description='Laser pulse repetition rate (kHz)',
                                       validators=[Optional(),
                                                   NumberRange(min=0, message='Frequency must be positive')])
    temperature = FloatField('Temperature', description='Temperature (K)', validators=[Optional()])
    detection_rate = FloatField('Detection Rate', description='Detection rate (%)', validators=[Optional()])
    chamber_pressure = FloatField('Chamber Vacuum Pressure', description='Chamber pressure (torr)',
                                  validators=[Optional()])
    misc = FieldList(FormField(KeyValueForm), 'Other Metadata', description='Anything else that is pertinent')


class APTSampleElectropolishingForm(Form):
    """Form for an electropolishing step"""

    solution = StringField('Solution', description='Electropolishing solution', validators=[Optional()])
    voltage = FloatField('Voltage', description='Electropolishing voltage (V)', validators=[Optional()])
    temperature = FloatField('Temperature', description='Electropolishing temperature (C)', validators=[Optional()])


class APTFIBLiftoutStepForm(Form):
    """Form for liftout_step"""

    capping_material = StringField('Capping Material', description='Capping material', validators=[Optional()])
    wedge_dimension = FloatField('Wedge Dimension', description='Wedge dimension (um)', validators=[Optional()])
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
    sample_form = FormField(APTSampleDescriptionForm, description="Metadata that describes the sample")
    collection_form = FormField(APTCollectionMethodForm, description="Metadata for data collection method")
    preparation_form = FormField(APTSamplePreparationForm, description="Metadata for sample preparation")
    rhit_file = FileField('RHIT file', validators=[Optional()])


class APTReconstructionForm(Form):
    """Form to describe metadata for a APT reconstruction"""

    title = StringField('Title', description='Title for this reconstruction')
    description = TextAreaField('Description', description='Longer-form description of this reconstruction')
    reconstruction_method = RadioField('Reconstruction Method', description='Method used to reconstruct APT data',
                                       choices=[('shank_angle', 'Shank Angle'), ('voltage_profile', 'Voltage Profile'),
                                                ('tip_image', 'Tip Image')], default='shank_angle')
    tip_radius = FloatField('Initial Tip Radius', description='Initial tip radius (nm)', render_kw={'min': 0},
                            validators=[Optional()])
    evaporation_field = FloatField('Evaporation field', description='Evaporation field strength (V/nm)',
                                   validators=[Optional()])
    initial_voltage = FloatField('Initial voltage', description='Initial voltage (V)', validators=[Optional()])
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


class PublicationForm(DatasetForm):
    """Form for publication into the MDF"""

    accept_license = BooleanField('Accept License', description='Do you accept the data license for NUCAPT?')
    contact_person = StringField('Contact Person', description='Main point of contact')
    contact_email = EmailField('Contact Email', description='Point of contact email')

    def convert_to_globus_publication(self):
        """Return the contents of the form in a way that is comptabile with Globus Publish's API.

        :return: dict, metadata in Publish-friendly format"""

        output = dict()

        # Required fields
        output['accept_license'] = self.data['accept_license']

        # DataCite fields
        output['dc.title'] = self.data['title']
        output['dc.publisher'] = 'Materials Data Facility'
        output['dc.date.issued'] = date.today().strftime("%Y-%m-%d")
        output['dc.contributor.author'] = ['%s, %s' % (x['last_name'], x['first_name']) for x in self.data['authors']]
        output['datacite.creator.affiliation'] = [x['affiliation'] for x in self.data['authors']]

        # MDF Fields
        output['mdf-base.data_acquisition_method'] = 'Atom probe tomography'
        output['mdf-base.primary_product'] = 'Data files'
        output['mdf-base.description'] = self.data['abstract']
        output['mdf-base.data_acquisition_location'] = 'NUCAPT'

        # TODO: Add MRR-related fields to data file
        return output


class AnalysisForm(Form):
    """Form for the results of a dataset analysis

    TODO: Consider adding fields where users can describe each file being uploaded. The idea would be that the
    form adds new fields after the user uploads the files"""

    title = StringField('Title', description='Short description of the analysis')
    folder_name = StringField('Folder Name', description='Name of folder to hold data.',
                              render_kw=dict(pattern='\\w+',
                                             title='Only word characters allowed: A-Z, a-z, 0-9, and _'),
                              validators=[Regexp('\\w+', message='Reconstruction name can only contain word '
                                                                 'characters: A-Z, a-z, 0-9, and _')])
    description = TextAreaField('Description', description='Description of what this analysis results are. It is good '
                                                           'practice to describe the contents of the files you will '
                                                           'be uploading.')
    files = FileField('Files', description='Files associated with this analysis', render_kw={'multiple': None})

    def get_presets(self):
        """Generate a list of pre-defined names and descriptions

        These lists are used within the website to pre-fill results

        :return: OrderedDict, where each item holds the values for the above forms"""

        return OrderedDict(conc_profile={
            'title': 'Concentration Profile',
            'folder_name': 'Concentration_Profile',
            'description': '1D concentration profile (e.g., proxigram)',
        }, mass_spec={
            'title': 'Mass Spectrum',
            'folder_name': 'Mass_Spectrum',
            'description': 'Spectrum of the mass to charge ratio'
        }, bulk_comp={
            'title': 'Bulk Composition',
            'folder_name': 'Bulk_Composition',
            'description': 'Bulk composition of the tip of region of interest'
        }, dist_analysis={
            'title': 'Distribution Analysis',
            'folder_name': 'Distribution_Analysis',
            'description': 'Spatial distribution analysis'
        }, twod_map={
            'title': '2D Map',
            'folder_name': '2D_Map',
            'description': 'Two dimensional projection of reconstruction'
        }, threed_map={
            'title': '3D Map',
            'folder_name': '3D_Map',
            'description': 'Three dimensional visualization of reconstruction'
        }
        )
