from flask import request, session

import globus_sdk
from globus_sdk.authorizers.refresh_token import RefreshTokenAuthorizer

from globus_nexus_client import NexusClient

try:
    from urllib.parse import urlparse, urljoin
except:
    from urlparse import urlparse, urljoin

from flask import current_app


def load_portal_client():
    """Create an AuthClient for the portal"""
    return globus_sdk.ConfidentialAppAuthClient(
        current_app.config['PORTAL_CLIENT_ID'],
        current_app.config['PORTAL_CLIENT_SECRET']
    )


def is_safe_redirect_url(target):
    """https://security.openstack.org/guidelines/dg_avoid-unvalidated-redirects.html"""  # noqa
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))

    return redirect_url.scheme in ('http', 'https') and \
        host_url.netloc == redirect_url.netloc


def get_safe_redirect():
    """https://security.openstack.org/guidelines/dg_avoid-unvalidated-redirects.html"""  # noqa
    url = request.args.get('next')
    if url and is_safe_redirect_url(url):
        return url

    url = request.referrer
    if url and is_safe_redirect_url(url):
        return url

    return '/'


def is_group_member():
    """Check whether authenticated user is a member of the NUCAPT group"""
    nexus_client = NexusClient(authorizer=RefreshTokenAuthorizer(session["tokens"]["nexus.api.globus.org"]
                                                                 ["refresh_token"], load_portal_client()))
    reply = nexus_client.list_groups(for_all_identities='true', my_roles=['admin', 'manager', 'member'])

    for group in reply.data:
        if group['id'] == current_app.config['GROUP_ID']:
            return group['my_status'] == 'active'
    return False