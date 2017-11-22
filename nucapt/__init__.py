from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('nucapt.conf')

app.config.update({
    'SCOPES': ['urn:globus:auth:scope:transfer.api.globus.org:all',
               'openid', 'email', 'profile',
               'https://auth.globus.org/scopes/ab24b500-37a2-4bad-ab66-d8232c18e6e5/publish_api'],
})

from nucapt import views
