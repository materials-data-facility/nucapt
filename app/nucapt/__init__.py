from flask import Flask

app = Flask(__name__)
app.config.from_envvar('APP_CONFIG_FILE')

app.config.update({
    'SCOPES': ['urn:globus:auth:scope:transfer.api.globus.org:all',
               'openid', 'email', 'profile',
               'https://auth.globus.org/scopes/ab24b500-37a2-4bad-ab66-d8232c18e6e5/publish_api',
               'https://auth.globus.org/scopes/c17f27bb-f200-486a-b785-2a25e82af505/connect'],
})
