from nucapt import app
from flask import render_template, request
from nucapt.forms import CreateForm

@app.route("/")
def index():
    """Render the home page"""
    return render_template('home.html')


@app.route("/create", methods=['GET', 'POST'])
def create():
    """Render the 'create new dataset' form"""

    form = CreateForm(request.form)
    if request.method == 'POST' and form.validate():
        print(form.data)
    return render_template('create.html', form=form)
