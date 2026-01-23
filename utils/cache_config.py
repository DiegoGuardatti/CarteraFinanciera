#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración de sistema de caching para Cartera Financiera
Optimiza el performance de APIs con Redis y cache en memoria
"""

import os
from flask import Flask
from flask_caching import Cache
from datetime import timedelta

def configure_cache(app: Flask):
    """
    Configura el sistema de caching para la aplicación Flask
    
    Args:
        app: Instancia de la aplicación Flask
    """
    # Configuración del cache basada en variables de entorno
    cache_config = {
        'CACHE_TYPE': os.environ.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300)),
        'CACHE_THRESHOLD': int(os.environ.get('CACHE_THRESHOLD', 500)),
    }
    
    # Si Redis está disponible, usarlo para mejor performance
    try:
        import redis
        
        # Usar la IP de Redis directamente (172.19.0.2)
        redis_host = '172.19.0.2'
        redis_port = 6379
        redis_db = 0
        redis_password = None
        
        # Intentar conectar con Redis
        test_redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)
        test_redis.ping()
        
        # Si Redis funciona, usar RedisCache
        cache_config.update({
            'CACHE_TYPE': 'RedisCache',
            'CACHE_REDIS_HOST': redis_host,
            'CACHE_REDIS_PORT': redis_port,
            'CACHE_REDIS_DB': redis_db,
            'CACHE_REDIS_PASSWORD': redis_password,
            'CACHE_DEFAULT_TIMEOUT': 600,  # 10 minutos para Redis
        })
        
        print("✅ Redis cache configurado exitosamente")
        
    except ImportError:
        print("⚠️ Redis no disponible, usando SimpleCache")
        print("   Para usar Redis, instalar con: pip install redis")
        # Mantener configuración por defecto
    except Exception as e:
        print(f"⚠️ Redis no disponible ({str(e)}), usando SimpleCache")
        # Mantener configuración por defecto
    
    # Aplicar configuración al app
    app.config.update(cache_config)
    
    # Inicializar cache
    cache = Cache(app)
    
    return cache

def get_cache_key_maker(prefix: str = "cartera"):
    """
    Crea una función para generar claves de cache consistentes
    
    Args:
        prefix: Prefijo para las claves
        
    Returns:
        función que genera claves con formato: prefix:función:params
    """
    from hashlib import md5
    from functools import wraps
    from flask import request
    
    def make_cache_key(*args, **kwargs):
        """Genera una clave única basada en función, argumentos y URL"""
        key_parts = [prefix]
        
        # Añadir nombre de la función
        if hasattr(args[0], '__name__'):
            key_parts.append(args[0].__name__)
        
        # Añadir parámetros de la función
        for arg in args[1:]:
            key_parts.append(str(arg))
        
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # Añadir parámetros de query string si existen
        if hasattr(request, 'query_string') and request.query_string:
            key_parts.append(f"query:{request.query_string.decode()}")
        
        # Generar clave usando MD5 para evitar claves muy largas
        key_string = ":".join(key_parts)
        return md5(key_string.encode()).hexdigest()
    
    return make_cache_key

def cache_with_params(timeout=None, key_func=None):
    """
    Decorator avanzado para caching con parámetros personalizables
    
    Args:
        timeout: Tiempo de expiración en segundos
        key_func: Función personalizada para generar claves
    """
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import current_app
            from flask_caching import Cache
            
            cache = current_app.extensions.get('cache')
            if not cache:
                return f(*args, **kwargs)
            
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{f.__name__}:{':'.join(map(str, args))}:{':'.join(f'{k}:{v}' for k, v in sorted(kwargs.items()))}"
            
            # Intentar obtener del cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Si no está en cache, ejecutar función
            result = f(*args, **kwargs)
            
            # Guardar en cache
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

# Configuraciones específicas para diferentes tipos de APIs
API_CACHE_CONFIG = {
    # Dashboard - cache más corto (30 segundos) por que cambia frecuentemente
    'dashboard': {
        'timeout': 30,
        'description': 'Dashboard con métricas en tiempo real'
    },
    
    # Métricas básicas - cache intermedio (2 minutos)
    'metricas_basicas': {
        'timeout': 120,
        'description': 'Métricas de ROI, Sharpe, VaR, etc.'
    },
    
    # Métricas avanzadas - cache más largo (5 minutos) por que son cálculos complejos
    'metricas_avanzadas': {
        'timeout': 300,
        'description': 'TIR, Beta, Alpha, correlación, etc.'
    },
    
    # Reportes - cache largo (15 minutos) por que son operaciones pesadas
    'reportes': {
        'timeout': 900,
        'description': 'Generación de reportes CSV, Excel, PDF'
    },
    
    # Gestión de datos - cache muy corto (15 segundos) por que cambian frecuentemente
    'datos_maestros': {
        'timeout': 15,
        'description': 'Brokers, comitentes, instrumentos, tickers'
    }
}

def get_cache_config_for_api(api_type: str):
    """
    Obtiene configuración de cache específica para un tipo de API
    
    Args:
        api_type: Tipo de API ('dashboard', 'metricas_basicas', etc.)
        
    Returns:
        dict: Configuración de cache
    """
    return API_CACHE_CONFIG.get(api_type, {
        'timeout': 300,  # Default 5 minutos
        'description': 'Cache por defecto'
    })

def invalidate_cache_pattern(pattern: str):
    """
    Invalida todas las claves de cache que coincidan con un patrón
    
    Args:
        pattern: Patrón de claves a invalidar
    """
    from flask import current_app
    
    cache = current_app.extensions.get('cache')
    if not cache:
        return
    
    try:
        if hasattr(cache, '_cache') and hasattr(cache._cache, 'keys'):
            # Para Redis
            if hasattr(cache._cache, 'keys'):
                keys = cache._cache.keys(pattern)
                if keys:
                    cache._cache.delete(*keys)
                    print(f"✅ Cache invalidado: {len(keys)} claves eliminadas")
        else:
            # Para SimpleCache, limpiar completamente
            cache.clear()
            print("✅ Cache SimpleCache limpiado completamente")
            
    except Exception as e:
        print(f"⚠️ Error invalidando cache: {str(e)}")

def get_cache_stats():
    """
    Obtiene estadísticas del cache
    
    Returns:
        dict: Estadísticas del cache
    """
    from flask import current_app
    
    cache = current_app.extensions.get('cache')
    if not cache:
        return {'error': 'Cache no configurado'}
    
    try:
        if hasattr(cache, '_cache'):
            # Para Redis
            if hasattr(cache._cache, 'info'):
                info = cache._cache.info()
                return {
                    'tipo': 'Redis',
                    'memoria_usada': info.get('used_memory_human', 'N/A'),
                    'conexiones_activas': info.get('connected_clients', 0),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
            else:
                # Para SimpleCache
                return {
                    'tipo': 'SimpleCache',
                    'elementos_cacheados': len(getattr(cache._cache, '_cache', {})),
                    'hits': getattr(cache._cache, 'hits', 0),
                    'misses': getattr(cache._cache, 'misses', 0)
                }
    except Exception as e:
        return {'error': f"Error obteniendo estadísticas: {str(e)}"}
    
    return {'tipo': 'Desconocido'}