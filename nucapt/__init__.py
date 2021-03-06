from flask import Flask
from flask_sslify import SSLify

# Load in the app
app = Flask(__name__)
app.config.from_pyfile('nucapt.conf')

# Redirect all HTTP traffic to HTTPS
sslify = SSLify(app)

if app.config['DEBUG_SKIP_AUTH']:
    print('WARNING: Skipping authorization for debugging purposes!')

app.config.update({
    'SCOPES': ['urn:globus:auth:scope:transfer.api.globus.org:all',
               'openid', 'email', 'profile',
               'https://auth.globus.org/scopes/ab24b500-37a2-4bad-ab66-d8232c18e6e5/publish_api',
               'urn:globus:auth:scope:nexus.api.globus.org:groups'],
})

from nucapt import views
