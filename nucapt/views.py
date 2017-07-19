from nucapt import app
from flask import render_template, request, redirect
from nucapt.forms import CreateForm, LEAPSampleForm
from nucapt.manager import APTDataDirectory, APTSampleDirectory
from nucapt.exceptions import DatasetParseException
from nucapt.metadata import APTSampleGeneralMetadata


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


@app.route("/datasets")
def list_datasets():
    """List all datasets currently stored at default data path"""

    dir_info = APTDataDirectory.get_all_datasets()
    dir_valid = dict([(dir, isinstance(info,APTDataDirectory)) for dir,info in dir_info.items()])
    return render_template("dataset_list.html", dir_info=dir_info, dir_valid=dir_valid)


@app.route("/dataset/<name>/sample/create", methods=['GET', 'POST'])
def create_sample(name):
    """Create a new sample for a dataset"""

    # Load in the dataset
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        return redirect('/dataset/' + name)

    # Initialize form data
    form = LEAPSampleForm()

    errors = None
    if form.validate_on_submit():
        # attempt to validate the metadata
        try:
            sample_name = APTSampleDirectory.create_sample(name, form)
        except DatasetParseException as err:
            return render_template('create_sample.html', form=form, name=name, errors=err.errors)
        return redirect("/dataset/%s/sample/%s"%(name, sample_name))

    return render_template('create_sample.html', form=form, name=name, errors=None)


@app.route("/dataset/<dataset_name>/sample/<sample_name>")
def view_sample(dataset_name, sample_name):
    """View metadata about sample"""

    # Load in the sample by name
    sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)

    # Load in the sample information
    sample_metadata = None
    collection_metadata = None
    errors = None
    try:
        sample_metadata = sample.load_sample_information()
        collection_metadata = sample.load_collection_metadata()
    except DatasetParseException as err:
        errors = err
    return render_template('sample.html', dataset_name=dataset_name, sample=sample,
                           sample_name=sample_name, sample_metadata=sample_metadata,
                           collection_metadata=collection_metadata, errors=errors)