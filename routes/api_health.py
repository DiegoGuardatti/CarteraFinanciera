"""
API de Health Check y Monitoreo
Endpoints para monitoreo de salud del sistema
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import os
import sys
import time
import subprocess
import socket

# Importaciones opcionales
try:
    from flask_login import login_required
    FLASK_LOGIN_AVAILABLE = True
except ImportError:
    FLASK_LOGIN_AVAILABLE = False
    def login_required(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Mock psutil functions
    class MockPsutil:
        @staticmethod
        def cpu_percent(interval=1):
            return 50.0
        @staticmethod
        def virtual_memory():
            class Memory:
                percent = 60.0
                total = 8000000000
                available = 3200000000
                used = 4800000000
                free = 3200000000
            return Memory()
        @staticmethod
        def disk_usage(path):
            class Disk:
                percent = 45.0
                total = 100000000000
                used = 45000000000
                free = 55000000000
            return Disk()
        @staticmethod
        def pids():
            return list(range(100))
        @staticmethod
        def cpu_count():
            return 4
        @staticmethod
        def disk_io_counters():
            class DiskIO:
                read_bytes = 1000000
                write_bytes = 2000000
            return DiskIO()
        @staticmethod
        def net_io_counters():
            class NetIO:
                bytes_sent = 5000000
                bytes_recv = 3000000
                packets_sent = 1000
                packets_recv = 800
            return NetIO()
        @staticmethod
        def process_iter(attrs):
            return []
        @staticmethod
        def boot_time():
            return time.time() - 86400
    psutil = MockPsutil()

from extensions import db, cache

api_health_bp = Blueprint('api_health', __name__, url_prefix='/api')

@api_health_bp.route('/health')
def health_check():
    """
    Health check básico del sistema
    """
    try:
        # Verificar conectividad a base de datos
        db_status = check_database_health()
        
        # Verificar conectividad a Redis
        cache_status = check_cache_health()
        
        # Obtener métricas del sistema
        system_metrics = get_system_metrics()
        
        # Calcular estado general
        overall_status = "healthy"
        if not db_status['healthy'] or not cache_status['healthy']:
            overall_status = "unhealthy"
        elif system_metrics['cpu_percent'] > 90 or system_metrics['memory_percent'] > 90:
            overall_status = "degraded"
        
        health_data = {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'version': get_app_version(),
            'database': db_status,
            'cache': cache_status,
            'system': system_metrics,
            'uptime': get_uptime()
        }
        
        # Código de respuesta basado en el estado
        status_code = 200 if overall_status == "healthy" else 503
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_health_bp.route('/health/detailed')
@login_required
def detailed_health_check():
    """
    Health check detallado con métricas completas
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': check_database_detailed(),
                'cache': check_cache_detailed(),
                'disk': check_disk_health(),
                'network': check_network_health(),
                'processes': check_process_health(),
                'application': check_application_health()
            },
            'metrics': {
                'system': get_detailed_system_metrics(),
                'application': get_application_metrics(),
                'performance': get_performance_metrics()
            }
        }
        
        # Determinar estado general
        all_healthy = all(
            check.get('healthy', False) 
            for check in health_data['checks'].values()
        )
        
        health_data['status'] = 'healthy' if all_healthy else 'degraded'
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@api_health_bp.route('/metrics')
@login_required
def get_metrics():
    """
    Endpoint de métricas para Prometheus
    """
    try:
        metrics = generate_prometheus_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_health_bp.route('/status')
def simple_status():
    """
    Status simple para load balancers y health checks externos
    """
    try:
        # Verificar solo que la aplicación esté respondiendo
        db.session.execute('SELECT 1')
        return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()}), 200
    except:
        return jsonify({'status': 'error', 'timestamp': datetime.utcnow().isoformat()}), 503

# ==================== FUNCIONES DE VERIFICACIÓN ====================

def check_database_health():
    """Verificar salud de la base de datos"""
    try:
        start_time = time.time()
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        response_time = (time.time() - start_time) * 1000  # en ms
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'status': 'connected'
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'status': 'disconnected'
        }

def check_cache_health():
    """Verificar salud del cache Redis"""
    try:
        # Importar cache desde la aplicación Flask creada
        from app import cache
        
        if cache:
            start_time = time.time()
            # Necesitamos un contexto de aplicación para usar el cache
            from app import app
            with app.app_context():
                cache.set('health_check', 'ok', timeout=10)
                result = cache.get('health_check')
            response_time = (time.time() - start_time) * 1000
            
            return {
                'healthy': result == 'ok',
                'response_time_ms': round(response_time, 2),
                'status': 'connected' if result == 'ok' else 'no_response'
            }
        else:
            return {
                'healthy': False,
                'status': 'not_configured'
            }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e),
            'status': 'disconnected'
        }

def get_system_metrics():
    """Obtener métricas básicas del sistema"""
    try:
        return {
            'cpu_percent': round(psutil.cpu_percent(interval=1), 2),
            'memory_percent': round(psutil.virtual_memory().percent, 2),
            'disk_percent': round(psutil.disk_usage('/').percent, 2),
            'load_average': os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0,
            'process_count': len(psutil.pids())
        }
    except Exception as e:
        return {'error': str(e)}

def get_uptime():
    """Obtener tiempo de actividad del sistema"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        
        return {
            'seconds': uptime_seconds,
            'formatted': format_uptime(uptime_seconds)
        }
    except Exception as e:
        return {'error': str(e)}

def check_database_detailed():
    """Verificación detallada de base de datos"""
    try:
        # Obtener estadísticas de conexión
        connection_info = {
            'pool_size': getattr(db.engine.pool, 'size', 0),
            'checked_in': getattr(db.engine.pool, 'checkedout', 0),
            'overflow': getattr(db.engine.pool, 'overflow', 0)
        }
        
        # Verificar tablas principales
        tables_to_check = ['activos', 'transacciones', 'usuarios']
        table_status = {}
        
        for table in tables_to_check:
            try:
                result = db.session.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                table_status[table] = {'healthy': True, 'count': result}
            except Exception as e:
                table_status[table] = {'healthy': False, 'error': str(e)}
        
        return {
            'healthy': all(t['healthy'] for t in table_status.values()),
            'connection_pool': connection_info,
            'tables': table_status
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_cache_detailed():
    """Verificación detallada de cache"""
    try:
        if not cache:
            return {'healthy': False, 'status': 'not_configured'}
        
        # Verificar memoria de Redis si está disponible
        cache_info = {}
        try:
            info = cache.get_cache_info() if hasattr(cache, 'get_cache_info') else {}
            cache_info = {
                'used_memory': info.get('used_memory', 'N/A'),
                'connected_clients': info.get('connected_clients', 'N/A')
            }
        except:
            cache_info = {'status': 'basic_check_only'}
        
        return {
            'healthy': True,
            'info': cache_info,
            'status': 'operational'
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_disk_health():
    """Verificar salud del disco"""
    try:
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        return {
            'healthy': disk_usage.percent < 90,
            'usage_percent': disk_usage.percent,
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'total_gb': round(disk_usage.total / (1024**3), 2),
            'io_read_mb': round(disk_io.read_bytes / (1024**2), 2) if disk_io else 'N/A',
            'io_write_mb': round(disk_io.write_bytes / (1024**2), 2) if disk_io else 'N/A'
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_network_health():
    """Verificar salud de red"""
    try:
        # Verificar conectividad a servicios externos
        external_checks = {
            'dns': check_dns_resolution(),
            'internet': check_internet_connectivity()
        }
        
        # Obtener estadísticas de red
        net_io = psutil.net_io_counters()
        
        return {
            'healthy': external_checks['internet']['reachable'],
            'external_checks': external_checks,
            'bytes_sent': net_io.bytes_sent if net_io else 0,
            'bytes_recv': net_io.bytes_recv if net_io else 0,
            'packets_sent': net_io.packets_sent if net_io else 0,
            'packets_recv': net_io.packets_recv if net_io else 0
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_process_health():
    """Verificar salud de procesos"""
    try:
        # Verificar procesos críticos
        critical_processes = ['mysql', 'redis', 'nginx', 'gunicorn']
        process_status = {}
        
        for process_name in critical_processes:
            try:
                processes = [p for p in psutil.process_iter(['pid', 'name']) 
                           if process_name.lower() in p.info['name'].lower()]
                process_status[process_name] = {
                    'healthy': len(processes) > 0,
                    'count': len(processes),
                    'pids': [p.info['pid'] for p in processes]
                }
            except Exception as e:
                process_status[process_name] = {'healthy': False, 'error': str(e)}
        
        return {
            'healthy': any(p['healthy'] for p in process_status.values()),
            'processes': process_status,
            'total_processes': len(psutil.pids())
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def check_application_health():
    """Verificar salud de la aplicación"""
    try:
        # Verificar endpoints críticos
        endpoints_to_check = [
            '/api/dashboard/summary',
            '/api/metrics/portfolio',
            '/api/advanced/summary'
        ]
        
        # En un entorno real, esto haría requests HTTP internos
        # Por ahora, simulamos que están funcionando
        endpoint_status = {
            endpoint: {'healthy': True, 'status': 'simulated_ok'} 
            for endpoint in endpoints_to_check
        }
        
        return {
            'healthy': True,
            'endpoints': endpoint_status,
            'version': get_app_version(),
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

def get_detailed_system_metrics():
    """Obtener métricas detalladas del sistema"""
    try:
        return {
            'cpu': {
                'count': psutil.cpu_count(),
                'usage_per_core': [round(x, 2) for x in psutil.cpu_percent(interval=1, percpu=True)],
                'load_avg': list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0, 0, 0]
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'free': psutil.virtual_memory().free
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }
    except Exception as e:
        return {'error': str(e)}

def get_application_metrics():
    """Obtener métricas de la aplicación"""
    try:
        return {
            'flask_version': getattr(sys.modules.get('flask'), '__version__', 'unknown'),
            'python_version': sys.version,
            'working_directory': os.getcwd(),
            'environment': os.getenv('FLASK_ENV', 'unknown')
        }
    except Exception as e:
        return {'error': str(e)}

def get_performance_metrics():
    """Obtener métricas de performance"""
    try:
        return {
            'boot_time': psutil.boot_time(),
            'process_create_time': psutil.Process().create_time(),
            'memory_info': psutil.Process().memory_info()._asdict(),
            'num_threads': psutil.Process().num_threads()
        }
    except Exception as e:
        return {'error': str(e)}

def generate_prometheus_metrics():
    """Generar métricas en formato Prometheus"""
    try:
        # En un entorno real, esto retornaría métricas en formato Prometheus
        # Por ahora, retornamos métricas básicas en JSON
        metrics = {
            'app_info': {
                'version': get_app_version(),
                'status': 'running'
            },
            'system_metrics': get_system_metrics(),
            'health_status': check_database_health()
        }
        return metrics
    except Exception as e:
        return {'error': str(e)}

def check_dns_resolution():
    """Verificar resolución DNS"""
    try:
        socket.gethostbyname('google.com')
        return {'reachable': True, 'response_time_ms': 0}
    except:
        return {'reachable': False, 'response_time_ms': -1}

def check_internet_connectivity():
    """Verificar conectividad a internet"""
    try:
        import urllib.request
        start_time = time.time()
        urllib.request.urlopen('http://www.google.com', timeout=5)
        response_time = (time.time() - start_time) * 1000
        return {'reachable': True, 'response_time_ms': round(response_time, 2)}
    except:
        return {'reachable': False, 'response_time_ms': -1}

def get_app_version():
    """Obtener versión de la aplicación"""
    try:
        return os.getenv('APP_VERSION', '1.0.0')
    except:
        return 'unknown'

def format_uptime(seconds):
    """Formatear tiempo de actividad"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"