"""
Lightweight middleware used across the project.
"""


class ActivityLogMiddleware:
    """
    Currently a pass-through hook. Kept as a dedicated middleware class
    (rather than folding logic into views) so that, as the app grows,
    cross-cutting request/response instrumentation — e.g. timing,
    request-id tagging for logs — has a single, obvious place to live
    without touching every view.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
