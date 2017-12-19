from flask import redirect, request, session, url_for
from functools import wraps

from flask.globals import current_app
from flask.helpers import flash
from flask.templating import render_template

from nucapt.exceptions import DatasetParseException
from nucapt.manager import APTDataDirectory
from nucapt.utils import is_group_member


def authenticated(fn):
    """Mark a route as requiring authentication."""
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        # Check whether user is logged in to Globus
        if not session.get('is_authenticated'):
            return redirect(url_for('login', next=request.url))

        # Check whether user is authorized to use this system
        if not current_app.config['DEBUG_SKIP_AUTH']:
            if not is_group_member():
                return render_template('groups.html')

        if request.path == '/logout':
            return fn(*args, **kwargs)

        return fn(*args, **kwargs)
    return decorated_function


def check_if_published(fn):
    """Mark a route as having edit access to a dataset.

    First argument is always the dataset name for these type of functions"""

    @wraps(fn)
    def decorated_function(*args, **kwargs):
        # Handle failures
        dataset_name = kwargs['dataset_name']
        try:
            data = APTDataDirectory.load_dataset_by_name(dataset_name)
        except DatasetParseException as exc:
            return redirect("/dataset/%s" % dataset_name)

        if data.is_published():
            flash('Dataset has already been published!', 'warning')
            return redirect("/dataset/%s" % dataset_name)

        # Pass it along
        return fn(*args, **kwargs)
    return decorated_function