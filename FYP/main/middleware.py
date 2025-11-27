from django.utils.deprecation import MiddlewareMixin

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Only disable cache for sensitive pages (login, admin, etc)
        # Allow caching for static pages like about, services, doctors, FAQ
        sensitive_paths = ['/admin', '/login', '/logout', '/diagnosis', '/Montoring', '/api/', '/password-reset']
        
        if any(request.path.startswith(path) for path in sensitive_paths):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        else:
            # Allow browser caching for static content pages (1 hour)
            response['Cache-Control'] = 'public, max-age=3600'
        
        return response
