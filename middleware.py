import time
import logging

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware:

    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        start = time.time()

        response = self.get_response(request)

        duration = time.time() - start

        logger.info(
            f"{request.method} {request.path} - {duration:.2f}s"
        )

        return response