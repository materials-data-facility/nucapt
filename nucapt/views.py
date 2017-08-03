import os
import shutil

from flask import render_template, request, redirect
from werkzeug.utils import secure_filename

from nucapt import app
from nucapt.exceptions import DatasetParseException
from nucapt.forms import DatasetForm, APTSampleForm, APTCollectionMethodForm, APTSampleDescriptionForm, \
    AddAPTReconstructionForm
from nucapt.manager import APTDataDirectory, APTSampleDirectory, APTReconstruction


@app.route("/")
def index():
    """Render the home page"""
    return render_template('home.html')


@app.route("/create", methods=['GET', 'POST'])
def create():
    """Create a new dataset"""
    title = 'Create New Dataset'
    description = 'Create a new dataset on the NUCAPT server. A dataset describes a single set of similar experiments.'

    form = DatasetForm(request.form)
    if request.method == 'POST' and form.validate():
        dataset = APTDataDirectory.initialize_dataset(form)
        return redirect('/dataset/%s'%dataset.name)
    return render_template('dataset_create.html', title=title, description=description, form=form)


@app.route("/dataset/<name>/edit", methods=['GET', 'POST'])
def edit_dataset(name):
    """Edit dataset metdata"""

    title = 'Edit Dataset'
    description = 'Edit the general metadata of a dataset'

    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except:
        return redirect("/dataset/" + name)

    if request.method == 'POST':
        form = DatasetForm(request.form)
        if form.validate():
            dataset.update_metadata(form)
            return redirect('/dataset/' + name)
        else:
            return render_template('dataset_create.html', title=title, description=description, form=form)
    else:
        form = DatasetForm(**dataset.get_metadata().metadata)
        return render_template('dataset_create.html', title=title, description=description, form=form)


@app.route("/dataset/<name>")
def display_dataset(name):
    """Display metadata about a certain dataset"""
    errors = []
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        dataset = None
        errors = exc.errors
    samples, sample_errors = dataset.list_samples()
    errors.extend(sample_errors)
    metadata = dataset.get_metadata()
    return render_template('dataset.html', name=name, dataset=dataset, samples=samples, errors=errors, metadata=metadata)


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
    form = APTSampleForm(request.form)

    if request.method == 'POST' and form.validate():
        # attempt to validate the metadata
        try:
            sample_name = APTSampleDirectory.create_sample(name, form)
        except DatasetParseException as err:
            return render_template('sample_create.html', form=form, name=name, errors=err.errors)

        # If valid, upload the data
        sample = APTSampleDirectory.load_dataset_by_name(name, sample_name)
        rhit_file = request.files['rhit_file']
        if rhit_file.filename.lower().endswith('.rhit'):
            rhit_file.save(os.path.join(sample.path, secure_filename(rhit_file.filename)))
        else:
            # Clear the old sample
            shutil.rmtree(sample.path)
            return render_template('sample_create.html', form=form, name=name, errors=['File must have extension RHIT'])

        return redirect("/dataset/%s/sample/%s"%(name, sample_name))

    return render_template('sample_create.html', form=form, name=name)


@app.route("/dataset/<dataset_name>/sample/<sample_name>")
def view_sample(dataset_name, sample_name):
    """View metadata about sample"""

    # Load in the sample by name
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return render_template('sample.html', dataset_name=dataset_name, sample=sample, errors=exc.errors)

    # Load in the sample information
    sample_metadata = None
    collection_metadata = None
    errors = []
    try:
        sample_metadata = sample.load_sample_information()
        collection_metadata = sample.load_collection_metadata()
        recon_data, recon_metadata, recon_errors = sample.list_reconstructions()
        errors.extend(recon_errors)
    except DatasetParseException as err:
        errors.extend(err.errors)
    return render_template('sample.html', dataset_name=dataset_name, sample=sample,
                           sample_name=sample_name, sample_metadata=sample_metadata,
                           collection_metadata=collection_metadata, errors=errors,
                           recon_data=list(zip(recon_data, recon_metadata)))


@app.route("/dataset/<dataset_name>/sample/<sample_name>/edit_info", methods=['GET', 'POST'])
def edit_sample_information(dataset_name, sample_name):
    """View metadata about sample"""

    # Load in the sample by name
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return redirect("/dataset/%s/sample/%s"%(dataset_name, sample_name))

    # Load in the metadata
    edit_page = 'sample_generalform.html'
    my_form = APTSampleDescriptionForm
    sample_metadata = sample.load_sample_information()
    updated_func = sample.update_sample_information

    return edit_sample_metadata(dataset_name, edit_page, my_form, sample, sample_metadata, sample_name, updated_func)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/edit_collection", methods=['GET', 'POST'])
def edit_collection_information(dataset_name, sample_name):
    """View metadata about sample"""

    # Load in the sample by name
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return redirect("/dataset/%s/sample/%s"%(dataset_name, sample_name))

    # Load in the metadata
    edit_page = 'sample_collectionform.html'
    my_form = APTCollectionMethodForm
    sample_metadata = sample.load_collection_metadata()
    updated_func = sample.update_collection_metadata

    return edit_sample_metadata(dataset_name, edit_page, my_form, sample, sample_metadata, sample_name, updated_func)


def edit_sample_metadata(dataset_name, edit_page, my_form, sample, sample_metadata, sample_name, update_func):
    """Utility function for editing sample metadata

    :param dataset_name: str, Name of dataset
    :param edit_page: str, Name of page to render
    :param my_form: cls, Form class
    :param sample: APTSampleDirectory, Object describing this sample
    :param sample_metadata: dict, Current metadata
    :param sample_name: str, name of sample
    :param update_func: function pointer, function to call with updated metadata
    :return:
    """
    if request.method == 'POST':
        # Validate the form
        form = my_form(request.form)
        errors = None
        if form.validate():
            try:
                update_func(form)
            except DatasetParseException as exc:
                errors = exc.errors
                return render_template(edit_page, dataset_name=dataset_name, sample=sample,
                                       sample_name=sample_name, errors=errors, form=form)
            return redirect('/dataset/%s/sample/%s' % (dataset_name, sample_name))
        else:
            return render_template(edit_page, dataset_name=dataset_name, sample=sample,
                                   sample_name=sample_name, errors=errors, form=form)
    else:
        # Load in the existing information
        errors = None
        try:
            form = my_form(**sample_metadata.metadata)
        except DatasetParseException as err:
            form = my_form()
            errors = err
        return render_template(edit_page, dataset_name=dataset_name, sample=sample,
                               sample_name=sample_name, form=form, errors=errors)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/recon/create", methods=['GET', 'POST'])
def create_reconstruction(dataset_name, sample_name):
    # Create the form
    form = AddAPTReconstructionForm(request.form)

    # Make sure it validates
    if request.method == 'POST' and form.validate():
        try:
            errors = []
            # check the file
            pos_file = request.files['pos_file']
            print(pos_file.filename)
            if not pos_file.filename.lower().endswith('.pos'):
                errors.append('File must have the extension ".pos"')

            # check the metadata
            recon_name = APTReconstruction.create_reconstruction(form, dataset_name, sample_name)
        except DatasetParseException as err:
            return render_template('reconstruction_create.html', form=form, dataset_name=dataset_name,
                                   sample_name=sample_name, errors=errors + err.errors)

        # If valid, upload the data
        recon = APTReconstruction.load_dataset_by_name(dataset_name, sample_name, recon_name)
        pos_file.save(os.path.join(recon.path, secure_filename(pos_file.filename)))

        return redirect("/dataset/%s/sample/%s/recon/%s" % (dataset_name, sample_name, recon_name))
    return render_template('reconstruction_create.html', form=form, dataset_name=dataset_name, sample_name=sample_name)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/recon/<recon_name>")
def view_reconstruction(dataset_name, sample_name, recon_name):
    errors = None
    try:
        # Load in the recon
        recon = APTReconstruction.load_dataset_by_name(dataset_name, sample_name, recon_name)
        recon_metadata = recon.load_metadata()
    except DatasetParseException as exc:
        errors = exc.errors
    return render_template('reconstruction.html', dataset_name=dataset_name, sample_name=sample_name,
                           recon_name=recon_name, recon=recon, recon_metadata=recon_metadata, errors=errors)
