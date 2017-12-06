import os
import shutil
import json

from flask import render_template, request, redirect, url_for, flash, session
from globus_sdk.auth.client_types.native_client import NativeAppAuthClient
from globus_sdk.authorizers.refresh_token import RefreshTokenAuthorizer
from globus_sdk.transfer.client import TransferClient
from mdf_toolbox.toolbox import DataPublicationClient
from werkzeug.utils import secure_filename
from mdf_toolbox import toolbox

from nucapt import app
from nucapt.exceptions import DatasetParseException
from nucapt.forms import DatasetForm, APTSampleForm, APTCollectionMethodForm, APTSampleDescriptionForm, \
    AddAPTReconstructionForm, APTSamplePreparationForm, PublicationForm
from nucapt.manager import APTDataDirectory, APTSampleDirectory, APTReconstruction
import nucapt.manager as manager
from nucapt.decorators import authenticated
from nucapt.utils import load_portal_client


@app.route("/")
def index():
    """Render the home page"""
    return render_template('home.html')


# GlobusAuth-related pages
@app.route('/login', methods=['GET'])
def login():
    """Send the user to Globus Auth."""
    return redirect(url_for('authcallback'))


@app.route('/authcallback', methods=['GET'])
def authcallback():
    """Handles the interaction with Globus Auth."""
    # If we're coming back from Globus Auth in an error state, the error
    # will be in the "error" query string parameter.
    if 'error' in request.args:
        flash("You could not be logged into the portal: " +
              request.args.get('error_description', request.args['error']))
        return redirect(url_for('home'))

    # Set up our Globus Auth/OAuth2 state
    redirect_uri = url_for('authcallback', _external=True)

    client = load_portal_client()
    client.oauth2_start_flow(redirect_uri,
                             refresh_tokens=True,
                             requested_scopes=app.config['SCOPES'])

    # If there's no "code" query string parameter, we're in this route
    # starting a Globus Auth login flow.
    if 'code' not in request.args:
        additional_authorize_params = (
            {'signup': 1} if request.args.get('signup') else {})

        auth_uri = client.oauth2_get_authorize_url(
            additional_params=additional_authorize_params)

        return redirect(auth_uri)
    else:
        # If we do have a "code" param, we're coming back from Globus Auth
        # and can start the process of exchanging an auth code for a token.
        code = request.args.get('code')
        tokens = client.oauth2_exchange_code_for_tokens(code)

        id_token = tokens.decode_id_token(client)
        session.update(
            tokens=tokens.by_resource_server,
            is_authenticated=True,
            name=id_token.get('name', ''),
            email=id_token.get('email', ''),
            institution=id_token.get('institution', ''),
            primary_username=id_token.get('preferred_username'),
            primary_identity=id_token.get('sub'),
        )

        return redirect(url_for('index'))


@authenticated
@app.route('/logout', methods=['GET'])
def logout():
    """
    - Revoke the tokens with Globus Auth.
    - Destroy the session state.
    - Redirect the user to the Globus Auth logout page.
    """
    client = load_portal_client()

    # Revoke the tokens with Globus Auth
    for token, token_type in (
            (token_info[ty], ty)
            # get all of the token info dicts
            for token_info in session['tokens'].values()
            # cross product with the set of token types
            for ty in ('access_token', 'refresh_token')
            # only where the relevant token is actually present
            if token_info[ty] is not None):
        client.oauth2_revoke_token(
            token, additional_params={'token_type_hint': token_type})

    # Destroy the session state
    session.clear()

    redirect_uri = url_for('index', _external=True)

    ga_logout_url = []
    ga_logout_url.append(app.config['GLOBUS_AUTH_LOGOUT_URI'])
    ga_logout_url.append('?client={}'.format(app.config['PORTAL_CLIENT_ID']))
    ga_logout_url.append('&redirect_uri={}'.format(redirect_uri))
    ga_logout_url.append('&redirect_name=NUCAPT DMS')

    # Redirect the user to the Globus Auth logout page
    return redirect(''.join(ga_logout_url))


@authenticated
@app.route("/create", methods=['GET', 'POST'])
def create():
    """Create a new dataset"""
    title = 'Create New Dataset'
    description = 'Create a new dataset on the NUCAPT server. A dataset describes a single set of similar experiments.'

    form = DatasetForm(request.form)
    if request.method == 'POST' and form.validate():
        dataset = APTDataDirectory.initialize_dataset(form)
        return redirect('/dataset/%s'%dataset.name)
    return render_template('dataset_create.html', title=title, description=description, form=form,
                           navbar=[('Create Dataset', '#')])


@authenticated
@app.route("/dataset/<name>/edit", methods=['GET', 'POST'])
def edit_dataset(name):
    """Edit dataset metadata"""

    title = 'Edit Dataset'
    description = 'Edit the general metadata of a dataset'
    navbar = [(name, '/dataset/%s'%name), ('Edit', '#')]

    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except (ValueError, AttributeError, DatasetParseException):
        return redirect("/dataset/" + name)

    if request.method == 'POST':
        form = DatasetForm(request.form)
        if form.validate():
            dataset.update_metadata(form)
            return redirect('/dataset/' + name)
        else:
            return render_template('dataset_create.html', title=title, description=description, form=form, navbar=navbar)
    else:
        form = DatasetForm(**dataset.get_metadata().metadata)
        return render_template('dataset_create.html', title=title, description=description, form=form, navbar=navbar)



@app.route("/dataset/<name>")
@authenticated
def display_dataset(name):
    """Display metadata about a certain dataset"""
    errors = []
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        dataset = None
        errors = exc.errors
        return render_template('dataset.html', name=name, dataset=dataset, errors=errors, navbar=[(name, '/dataset/%s' % name)])
    samples, sample_errors = dataset.list_samples()
    errors.extend(sample_errors)
    metadata = dataset.get_metadata()
    return render_template('dataset.html', name=name, dataset=dataset, samples=samples, errors=errors,
                           metadata=metadata, navbar=[(name, '/dataset/%s'%name)])


@app.route("/dataset/<name>/publish", methods=['GET', 'POST'])
@authenticated
def publish_dataset(name):
    """Publish a dataset to the Materials Data Facility"""

    # Check that this is a good dataset
    try:
        data = APTDataDirectory.load_dataset_by_name(name)
    except (ValueError, AttributeError, DatasetParseException):
        return redirect("/dataset/" + name)

    # Check if the dataset has already been published
    if data.is_published():
        return redirect("/dataset/" + name)

    if request.method == 'POST':
        # Get the user data
        form = PublicationForm(request.form)
        if not form.validate():
            raise Exception('Form failed to validate')


        # Create the PublicationClient
        globus_publish_client = DataPublicationClient(authorizer=
                                                      RefreshTokenAuthorizer(session["tokens"]["publish.api.globus.org"]
                                                                             ["refresh_token"], load_portal_client()))

        # Create the transfer client
        mdf_transfer_client = TransferClient(authorizer=
                                             RefreshTokenAuthorizer(session["tokens"]["transfer.api.globus.org"]
                                                                    ["refresh_token"], load_portal_client()))

        # For debugging, do not submit anything to Publish
        if app.config.get('DEBUG_SKIP_PUB', False):
            return redirect('/dataset/' + name)

        # Create the publication entry
        try:
            md_result = globus_publish_client.push_metadata(app.config.get("PUBLISH_COLLECTION"), form.data)
            pub_endpoint = md_result['globus.shared_endpoint.name']
            pub_path = os.path.join(md_result['globus.shared_endpoint.path'], "data") + "/"
            submission_id = md_result["id"]
        except Exception as e:
            # TODO: Update status - not Published due to bad metadata
            raise e

        # Transfer data
        try:
            # '/' of the Globus endpoint for the working data is the working data path
            data_path = '/%s/'%(os.path.relpath(data.path, manager.data_path))
            toolbox.quick_transfer(mdf_transfer_client, app.config["WORKING_DATA_ENDPOINT"],
                                   pub_endpoint, [(data_path, pub_path)], timeout=-1)
        except Exception as e:
            # TODO: Update status - not Published due to failed Transfer
            raise e
            # Complete submission

        # Mark dataset as complete.
        landing_url = None
        data.mark_as_published(submission_id, landing_url)

        # Redirect to Globus Publish webpage
        return redirect("/dataset/" + name)
    else:
        form = PublicationForm(**data.get_metadata().metadata)

        return render_template("dataset_publish.html", data=data, form=form)

@app.route("/datasets")
@authenticated
def list_datasets():
    """List all datasets currently stored at default data path"""

    dir_info = APTDataDirectory.get_all_datasets(manager.data_path)
    dir_valid = dict([(dir, isinstance(info,APTDataDirectory)) for dir,info in dir_info.items()])
    return render_template("dataset_list.html", dir_info=dir_info, dir_valid=dir_valid,
                           navbar=[('List Datasets', '#')])


@app.route("/dataset/<name>/sample/create", methods=['GET', 'POST'])
@authenticated
def create_sample(name):
    """Create a new sample for a dataset"""

    navbar = [(name, 'dataset/%s'%name), ('Create Sample', '#')]

    # Load in the dataset
    try:
        dataset = APTDataDirectory.load_dataset_by_name(name)
    except DatasetParseException as exc:
        return redirect('/dataset/' + name)

    # Initialize form data
    form = APTSampleForm(request.form) \
        if request.method == 'POST' \
        else APTSampleForm(sample_name='Sample%d'%(len(dataset.list_samples()[0])+1))

    if request.method == 'POST' and form.validate():
        # attempt to validate the metadata
        try:
            sample_name = APTSampleDirectory.create_sample(name, form)
        except DatasetParseException as err:
            return render_template('sample_create.html', form=form, name=name, errors=err.errors, navbar=navbar)

        # If valid, upload the data
        sample = APTSampleDirectory.load_dataset_by_name(name, sample_name)
        rhit_file = request.files['rhit_file']
        if rhit_file.filename.lower().endswith('.rhit'):
            rhit_file.save(os.path.join(sample.path, secure_filename(rhit_file.filename)))
        else:
            # Clear the old sample
            shutil.rmtree(sample.path)
            return render_template('sample_create.html', form=form, name=name, errors=['File must have extension RHIT'],
                                   navbar=navbar)

        return redirect("/dataset/%s/sample/%s"%(name, sample_name))

    # If GET request, make a new sample name
    return render_template('sample_create.html', form=form, name=name, navbar=navbar)


@app.route("/dataset/<dataset_name>/sample/<sample_name>")
@authenticated
def view_sample(dataset_name, sample_name):
    """View metadata about sample"""

    navbar = [(dataset_name, '/dataset/%s'%dataset_name), (sample_name, '#')]

    # Load in the sample by name
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return render_template('sample.html', dataset_name=dataset_name, sample=sample, errors=exc.errors, navbar=navbar)

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
        recon_data = []
        recon_metadata = []
    return render_template('sample.html', dataset_name=dataset_name, sample=sample,
                           sample_name=sample_name, sample_metadata=sample_metadata,
                           collection_metadata=collection_metadata, errors=errors,
                           recon_data=list(zip(recon_data, recon_metadata)),
                           navbar=navbar)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/edit_info", methods=['GET', 'POST'])
@authenticated
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
@authenticated
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


@app.route("/dataset/<dataset_name>/sample/<sample_name>/edit_preparation", methods=['GET', 'POST'])
@authenticated
def edit_sample_preparation(dataset_name, sample_name):
    """View metadata about sample"""

    # Load in the sample by name
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return redirect("/dataset/%s/sample/%s"%(dataset_name, sample_name))

    # Load in the metadata
    edit_page = 'sample_prepform.html'
    my_form = APTSamplePreparationForm
    try:
        sample_metadata = sample.get_preparation_metadata()
    except DatasetParseException as exc:
        print(exc.errors)

    updated_func = sample.update_preparation_metadata

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

    navbar = [(dataset_name, '/dataset/%s' % dataset_name),
              (sample_name, '/dataset/%s/sample/%s' % (dataset_name, sample_name)),
              ('Edit', '#')]

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
                                   sample_name=sample_name, errors=errors, form=form, navbar=navbar)
    else:
        # Load in the existing information
        errors = None
        try:
            form = my_form(**sample_metadata.metadata)
        except DatasetParseException as err:
            form = my_form()
            errors = err
        return render_template(edit_page, dataset_name=dataset_name, sample=sample,
                               sample_name=sample_name, form=form, errors=errors, navbar=navbar)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/recon/create", methods=['GET', 'POST'])
@authenticated
def create_reconstruction(dataset_name, sample_name):
    navbar = [(dataset_name, '/dataset/%s' % dataset_name),
              (sample_name, '/dataset/%s/sample/%s' % (dataset_name, sample_name)),
              ('Add Reconstruction', '#')]

    # Make sure this sample exists
    try:
        sample = APTSampleDirectory.load_dataset_by_name(dataset_name, sample_name)
    except DatasetParseException as exc:
        return redirect("/dataset/%s/sample/%s"%(dataset_name, sample_name))

    # Create the form
    form = AddAPTReconstructionForm(request.form) \
            if request.method == 'POST' \
            else AddAPTReconstructionForm(name='Reconstruction%d'%(len(sample.list_reconstructions()[0]) + 1))

    # Make sure it validates
    if request.method == 'POST' and form.validate():
        try:
            errors = []

            # check the files
            pos_file = request.files['pos_file']
            if not pos_file.filename.lower().endswith('.pos'):
                errors.append('POS File must have the extension ".pos"')

            rrng_file = request.files['rrng_file']
            if not rrng_file.filename.lower().endswith('.rrng'):
                errors.append('RRNG File must have extension ".rrng"')

            # Find if there is a tip image
            tip_image_path = None
            if 'tip_image' in request.files:
                tip_image = request.files['tip_image']
                tip_image_path = 'tip_image.%s' % (tip_image.filename.split(".")[-1])

            # If errors, raise
            if len(errors) > 0:
                raise DatasetParseException(errors)

            # check the metadata
            recon_name = APTReconstruction.create_reconstruction(form, dataset_name, sample_name, tip_image_path)
        except DatasetParseException as err:
            return render_template('reconstruction_create.html', form=form, dataset_name=dataset_name,
                                   sample_name=sample_name, errors=errors + err.errors, navbar=navbar)

        # If valid, upload the data
        recon = APTReconstruction.load_dataset_by_name(dataset_name, sample_name, recon_name)
        pos_file.save(os.path.join(recon.path, secure_filename(pos_file.filename)))
        rrng_file.save(os.path.join(recon.path, secure_filename(rrng_file.filename)))
        if 'tip_image' in request.files:
            tip_image = request.files['tip_image']
            tip_image.save(os.path.join(recon.path, 'tip_image.%s'%(tip_image.filename.split(".")[-1])))

        return redirect("/dataset/%s/sample/%s/recon/%s" % (dataset_name, sample_name, recon_name))

    return render_template('reconstruction_create.html', form=form, dataset_name=dataset_name,
                           sample_name=sample_name, navbar=navbar)


@app.route("/dataset/<dataset_name>/sample/<sample_name>/recon/<recon_name>")
@authenticated
def view_reconstruction(dataset_name, sample_name, recon_name):
    navbar = [(dataset_name, '/dataset/%s' % dataset_name),
              (sample_name, '/dataset/%s/sample/%s' % (dataset_name, sample_name)),
              (recon_name, '#')]

    errors = []
    try:
        # Load in the recon
        recon = APTReconstruction.load_dataset_by_name(dataset_name, sample_name, recon_name)
        recon_metadata = recon.load_metadata()
    except DatasetParseException as exc:
        errors = exc.errors

    pos_path = None
    rrng_path = None
    try:
        # Get the POS and RRNG files
        pos_path = recon.get_pos_file()
        rrng_path = recon.get_rrng_file()

    except DatasetParseException as exc:
        errors.extend(exc.errors)
    except:
        raise
    return render_template('reconstruction.html', dataset_name=dataset_name, sample_name=sample_name,
                           recon_name=recon_name, recon=recon, recon_metadata=recon_metadata, errors=errors,
                           pos_path=pos_path, rrng_path=rrng_path, navbar=navbar)
