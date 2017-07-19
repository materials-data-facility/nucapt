from flask import Flask
from flask_wtf import CSRFProtect

csrf = CSRFProtect()
app = Flask(__name__)
csrf.init_app(app)
app.secret_key = 'secrete_key...shhhh'

from nucapt import views
