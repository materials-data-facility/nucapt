from flask import Flask
from flask_wtf import CSRFProtect
from os import urandom

csrf = CSRFProtect()
app = Flask(__name__)
csrf.init_app(app)
app.secret_key = urandom(24)

from nucapt import views
