from flask import Flask
from flask_htpasswd import HtPasswdAuth

app = Flask(__name__)
app.config.from_pyfile('nucapt.conf')

if not app.config['DEBUG_SKIP_AUTH']:
    htpasswd = HtPasswdAuth(app)
else:
    print('WARNING: Authentication was disabled!')

app.config.update({
    'SCOPES': ['urn:globus:auth:scope:transfer.api.globus.org:all',
               'openid', 'email', 'profile',
               'https://auth.globus.org/scopes/ab24b500-37a2-4bad-ab66-d8232c18e6e5/publish_api'],
})

from nucapt import views
