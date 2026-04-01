from django.http import JsonResponse


class HealthCheckMiddleware:
    """
    Intercepts /api/health/ before Django's ALLOWED_HOSTS check.
    ALB health checks arrive with the container's private IP as
    the Host header, which Django rejects. This middleware responds
    early, bypassing that check.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/health/":
            return JsonResponse({"status": "ok"})
        return self.get_response(request)
