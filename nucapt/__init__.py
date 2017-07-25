from flask import Flask
from flask_wtf import CSRFProtect

app = Flask(__name__)

from nucapt import views
