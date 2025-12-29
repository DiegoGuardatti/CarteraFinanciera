"""
Configuración de seguridad para la aplicación Flask
"""

from flask import request, make_response
import logging

def setup_security_headers(app):
    """Configurar headers de seguridad para la aplicación"""
    
    @app.after_request
    def set_security_headers(response):
        """Establece headers de seguridad en todas las respuestas"""
        
        # Content Security Policy (CSP) - Previene XSS
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com https://stackpath.bootstrapcdn.com https://ajax.googleapis.com https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com https://cdn.plot.ly https://fonts.googleapis.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HTTP Strict Transport Security (HSTS) - Fuerza HTTPS
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-Content-Type-Options - Previene MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options - Previene clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection - Filtro XSS del navegador
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy - Controla la información de referrer
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy - Controla APIs del navegador
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'fullscreen=(self), '
            'sync-xhr=(self)'
        )
        
        # Cache-Control para APIs sensibles
        if request.path.startswith('/api/'):
            if 'metrics' in request.path or 'dashboard' in request.path:
                # APIs de métricas pueden ser cacheadas por 1 minuto
                response.headers['Cache-Control'] = 'public, max-age=60'
            else:
                # Otras APIs no deben ser cacheadas
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        
        return response

def setup_logging(app):
    """Configurar sistema de logging"""
    if not app.debug and not app.testing:
        import os
        os.makedirs('logs', exist_ok=True)
        file_handler = logging.FileHandler('logs/cartera.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 Cartera Financiera iniciada')

def configure_security(app):
    """Configurar todas las opciones de seguridad"""
    setup_security_headers(app)
    setup_logging(app)