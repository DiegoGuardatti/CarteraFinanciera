/**
 * SERVICE WORKER - CARTERA FINANCIERA
 * Progressive Web App con caching avanzado
 */

// Configuración de cache
const CACHE_NAME = 'cartera-financiera-v1.0.0';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';
const API_CACHE = 'api-v1';

// Recursos críticos para cache inmediato
const STATIC_ASSETS = [
  '/',
  '/static/estilos.css',
  '/static/funciones.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Endpoints de API para cache
const API_ENDPOINTS = [
  '/get_instrumentos_financieros',
  '/get_brokers',
  '/api/dashboard/summary',
  '/api/metrics/portfolio',
  '/api/advanced/summary'
];

// Instalar Service Worker
self.addEventListener('install', event => {
  console.log('🚀 Service Worker: Instalando...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('📦 Service Worker: Cacheando recursos estáticos');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('✅ Service Worker: Recursos estáticos cacheados');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('❌ Service Worker: Error cacheando recursos:', error);
      })
  );
});

// Activar Service Worker
self.addEventListener('activate', event => {
  console.log('⚡ Service Worker: Activando...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            // Limpiar caches antiguos
            if (cacheName !== STATIC_CACHE && 
                cacheName !== DYNAMIC_CACHE && 
                cacheName !== API_CACHE) {
              console.log('🗑️ Service Worker: Eliminando cache antiguo:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker: Activado correctamente');
        return self.clients.claim();
      })
  );
});

// Interceptar requests (Fetch Strategy)
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Solo manejar requests del mismo origen
  if (url.origin !== location.origin) {
    return;
  }
  
  // Estrategia diferente según el tipo de recurso
  if (isStaticAsset(request)) {
    // Cache First para assets estáticos
    event.respondWith(cacheFirst(request));
  } else if (isAPIRequest(request)) {
    // Network First para APIs con fallback de cache
    event.respondWith(networkFirst(request));
  } else if (isNavigationRequest(request)) {
    // Network First para páginas con cache fallback
    event.respondWith(networkFirst(request, '/'));
  } else {
    // Stale While Revalidate para otros recursos
    event.respondWith(staleWhileRevalidate(request));
  }
});

// Estrategias de cache

/**
 * Cache First: Busca en cache primero, luego en red
 */
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    // Cachear respuesta exitosa
    if (networkResponse.status === 200) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('Cache First error:', error);
    throw error;
  }
}

/**
 * Network First: Busca en red primero, luego en cache
 */
async function networkFirst(request, fallback) {
  try {
    const networkResponse = await fetch(request);
    
    // Cachear respuesta exitosa de API
    if (isAPIRequest(request) && networkResponse.status === 200) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('🌐 Network failed, trying cache for:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback para navegación
    if (fallback) {
      const fallbackResponse = await caches.match(fallback);
      if (fallbackResponse) {
        return fallbackResponse;
      }
    }
    
    throw error;
  }
}

/**
 * Stale While Revalidate: Sirve del cache y actualiza en background
 */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then(networkResponse => {
    if (networkResponse.status === 200) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  });
  
  return cachedResponse || fetchPromise;
}

// Detectar tipos de request
function isStaticAsset(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/static/') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.ico') ||
    url.hostname.includes('cdn') ||
    url.hostname.includes('fontawesome')
  );
}

function isAPIRequest(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/get_') ||
    API_ENDPOINTS.some(endpoint => url.pathname.includes(endpoint))
  );
}

function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

// Mensajes del cliente
self.addEventListener('message', event => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;
      
    case 'CLEAR_CACHE':
      clearAllCaches()
        .then(() => event.ports[0].postMessage({ success: true }))
        .catch(error => event.ports[0].postMessage({ error: error.message }));
      break;
      
    default:
      console.log('Unknown message type:', type);
  }
});

// Limpiar todos los caches
async function clearAllCaches() {
  const cacheNames = await caches.keys();
  return Promise.all(cacheNames.map(name => caches.delete(name)));
}

// Manejo de errores global
self.addEventListener('error', event => {
  console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', event => {
  console.error('Service Worker unhandled rejection:', event.reason);
});

console.log('🚀 Service Worker cargado correctamente');