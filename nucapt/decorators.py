from flask import redirect, request, session, url_for
from functools import wraps

from flask.helpers import flash

from nucapt.exceptions import DatasetParseException
from nucapt.manager import APTDataDirectory


def authenticated(fn):
    """Mark a route as requiring authentication."""
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if not session.get('is_authenticated'):
            return redirect(url_for('login', next=request.url))

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