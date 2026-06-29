"""
Context processors make a value available to every template without
each view having to pass it in manually. We use this for the
dark/light theme cookie and for global site metadata (name, version).
"""
from django.conf import settings


def theme_preference(request):
    """
    Reads the 'theme' cookie (set client-side by theme-toggle.js) so
    the server-rendered HTML can include the correct class on <html>
    on first paint, avoiding a flash of the wrong theme.
    """
    theme = request.COOKIES.get('theme', 'light')
    if theme not in ('light', 'dark'):
        theme = 'light'
    return {'current_theme': theme}


def site_metadata(request):
    return {
        'SITE_NAME': 'TaskFlow',
        'SITE_TAGLINE': 'Plan less, do more.',
    }
