from nucapt import app
from flask import render_template, request, redirect
from nucapt.forms import CreateForm, LEAPSampleForm
from nucapt.manager import APTDataDirectory
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTDataCollectionMetadata


@app.route("/")
def index():
    """Render the home page"""
    return render_template('home.html')


@app.route("/create", methods=['GET', 'POST'])
def create():
    """Create a new dataset"""
    form = CreateForm()
    if form.validate_on_submit():
        name, path = APTDataDirectory.initialize_dataset(
            form.title.data,
            form.abstract.data,
            form.authors.data
        )
        return redirect('/dataset/%s'%name)
    return render_template('create.html', form=form)


@app.route("/dataset/<name>")
def display_dataset(name):
    """Display metadata about a certain dataset"""
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
        errors = None
    except DatasetParseException as exc:
        dataset = None
        errors = exc.errors
    return render_template('dataset.html', name=name, dataset=dataset, errors=errors)


@app.route("/dataset/<name>/sample/create", methods=['GET', 'POST'])
def create_sample(name):
    """Create a new sample for a dataset"""

    # Load in the dataset
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        return redirect('/dataset/' + name)

    # Initialize form data
    # if len(request.form) is 0:
    #     try:
    #         metadata = dataset.load_collection_metadata()
    #     except DatasetParseException as err:
    #         return render_template('create_sample.html', form=None, name=name, errors=err.errors)
    #     form = LEAPMetadataForm(**metadata.metadata) if metadata is not None else LEAPMetadataForm(request.form)
    # else:
    form = LEAPSampleForm()

    # Update values, if need be
    # if request.method == 'POST' and form.validate():
    #     try:
    #         metadata = APTDataCollectionMetadata.from_form(form)
    #     except DatasetParseException as err:
    #         return render_template('create_sample.html', form=form, name=name, errors=err.errors)
    #     dataset.update_collection_metadata(metadata)
    #     return redirect('/dataset/%s'%name)
    return render_template('create_sample.html', form=form, name=name, errors=None)


@app.route("/datasets")
def list_datasets():
    """List all datasets currently stored at default data path"""

    dir_info = APTDataDirectory.get_all_datasets()
    dir_valid = dict([(dir, isinstance(info,APTDataDirectory)) for dir,info in dir_info.items()])
    return render_template("dataset_list.html", dir_info=dir_info, dir_valid=dir_valid)