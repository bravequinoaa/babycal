from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def parent_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_parent:
            raise PermissionDenied("Parents only.")
        return view_func(request, *args, **kwargs)

    return _wrapped
