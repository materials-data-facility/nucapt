from nucapt import app
from flask import render_template, request, redirect
from nucapt.forms import CreateForm, LEAPMetadataForm
from nucapt.manager import APTDataDirectory, DatasetParseException, APTDataCollectionMetadata


@app.route("/")
def index():
    """Render the home page"""
    return render_template('home.html')


@app.route("/create", methods=['GET', 'POST'])
def create():
    """Render the 'create new dataset' form"""
    form = CreateForm(request.form)
    if request.method == 'POST' and form.validate():
        name, path = APTDataDirectory.initialize_dataset(
            form.title.data,
            form.abstract.data,
            form.authors.data
        )
        return redirect('/dataset/%s'%name)
    return render_template('create.html', form=form)

@app.route("/dataset/<name>")
def display_dataset(name):
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
        errors = None
    except DatasetParseException as exc:
        dataset = None
        errors = exc.errors
    return render_template('dataset.html', name=name, dataset=dataset, errors=errors)

@app.route("/dataset/<name>/leapdata", methods=['GET', 'POST'])
def leap_metadata(name):

    # Load in the dataset
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        return redirect('/dataset/' + name)

    # Initialize form data
    if len(request.form) is 0:
        metadata = dataset.load_collection_metadata()
        if metadata is not None:
            form = LEAPMetadataForm(**metadata.metadata)
        print(form.data)
    else:
        form = LEAPMetadataForm(request.form)

    # Update values, if need be
    if request.method == 'POST' and form.validate():
        try:
            print(form.data)
            metadata = APTDataCollectionMetadata.from_form(form)
        except DatasetParseException as err:
            return render_template('leap_conditions.html', form=form, name=name, errors=err.errors)
        dataset.update_collection_metadata(metadata)
        return redirect('/dataset/%s'%name)
    return render_template('leap_conditions.html', form=form, name=name)