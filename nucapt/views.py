from nucapt import app
from flask import render_template, request, redirect
from nucapt.forms import CreateForm
from nucapt.manager import APTDataDirectory, DatasetParseException

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
