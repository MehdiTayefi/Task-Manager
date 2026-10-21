from .api.services import cleanup_expired


class DemoCleanupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cleanup_expired(batch_size=100)
        return self.get_response(request)
