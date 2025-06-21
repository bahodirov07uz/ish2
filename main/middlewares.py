# middlewares.py
from django.utils.timezone import now

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Faqatgina real foydalanuvchilarni hisobga olish (static, media emas)
        if request.path != '/favicon.ico' and not request.path.startswith('/static'):
            print(f"User IP: {get_client_ip(request)} - Time: {now()} - Path: {request.path}")

        return response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
