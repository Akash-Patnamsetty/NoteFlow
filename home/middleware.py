class NoCacheMiddleware:
    """
    Prevents the browser from serving pages out of its back-forward cache
    (bfcache) after the user has signed out. Without this, clicking the
    Back button after logout can repaint a page (e.g. settings.html) that
    was rendered while the user was still logged in — the browser just
    shows its in-memory snapshot instead of asking the server again, so
    @login_required never gets a chance to redirect to the login page.

    Setting Cache-Control: no-store tells the browser "don't keep this
    response around at all" — that forces a real network request on Back,
    which then correctly triggers the login redirect if the session is gone.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response