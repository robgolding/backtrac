from django.conf import settings

def static_url(request):
    url = getattr(settings, 'STATIC_URL', '/media/')
    return {'STATIC_URL': url}
