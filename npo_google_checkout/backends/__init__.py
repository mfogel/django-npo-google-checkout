"""
Logic adapted from ubernostrum's django-registration.
https://bitbucket.org/ubernostrum/django-registration/src/d36a38202ee3/registration/backends/__init__.py
"""

from django.core.exceptions import ImproperlyConfigured


# Python 2.7 has an importlib with import_module; for older Pythons,
# Django's bundled copy provides it.
try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

def get_backend(path):
    """
    Return an instance of a npo-google-checkout backend, given the dotted
    Python import path (as a string) to the backend class.

    If the backend cannot be located (e.g., because no such module
    exists, or because the module does not contain a class of the
    appropriate name), ``django.core.exceptions.ImproperlyConfigured``
    is raised.

    """
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error loading npo-google-checkout backend %s: "%s"' % (module, e))
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a npo-google-checkout backend named "%s"' % (module, attr))
    return backend_class()

