from wtforms import Form, StringField, TextAreaField, FieldList, FormField


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