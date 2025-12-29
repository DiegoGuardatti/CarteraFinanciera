// ========================================
// CARTERA FINANCIERA - JAVASCRIPT MODERNO
// Funciones mejoradas con UX avanzada y PWA
// ========================================

// Configuración global
const CONFIG = {
    API_BASE: '/',
    LOADING_DELAY: 300, // ms para mostrar indicador de carga
    TIMEOUT_REQUEST: 30000, // 30 segundos
    TOAST_DURATION: 5000, // 5 segundos
    THEME_KEY: 'cartera-theme',
    SIDEBAR_KEY: 'cartera-sidebar-collapsed',
    PWA_ENABLED: 'serviceWorker' in navigator
};

// Clase para manejo de notificaciones toast
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Crear contenedor de toast si no existe
        if (!document.getElementById('toast-container')) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.className = 'toast-container position-fixed top-0 end-0 p-3';
            this.container.style.zIndex = '9999';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('toast-container');
        }
    }

    show(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
        const toastId = 'toast-' + Date.now();
        const toastClass = type === 'success' ? 'text-bg-success' : 
                          type === 'error' ? 'text-bg-danger' : 
                          type === 'warning' ? 'text-bg-warning' : 'text-bg-info';

        const toastHTML = `
            <div id="${toastId}" class="toast ${toastClass}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas ${this.getIcon(type)} me-2"></i>
                    <strong class="me-auto">${this.getTitle(type)}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        this.container.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();

        // Remover del DOM cuando se oculta
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });

        return toast;
    }

    getIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    getTitle(type) {
        const titles = {
            success: 'Éxito',
            error: 'Error',
            warning: 'Advertencia',
            info: 'Información'
        };
        return titles[type] || titles.info;
    }
}

// Clase para manejo de indicadores de carga
class LoadingManager {
    constructor() {
        this.activeLoaders = new Map();
    }

    show(elementId, message = 'Cargando...') {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Si ya hay un loader activo, no crear otro
        if (this.activeLoaders.has(elementId)) return;

        const loaderHTML = `
            <div class="d-flex justify-content-center align-items-center" style="min-height: 100px;">
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">${message}</small>
                    </div>
                </div>
            </div>
        `;

        // Guardar contenido original
        this.activeLoaders.set(elementId, element.innerHTML);
        element.innerHTML = loaderHTML;
        element.setAttribute('data-loading', 'true');
    }

    hide(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Restaurar contenido original
        const originalContent = this.activeLoaders.get(elementId);
        if (originalContent) {
            element.innerHTML = originalContent;
            this.activeLoaders.delete(elementId);
        }
        element.removeAttribute('data-loading');
    }

    hideAll() {
        this.activeLoaders.forEach((_, elementId) => {
            this.hide(elementId);
        });
        this.activeLoaders.clear();
    }
}

// Clase para validación de formularios
class FormValidator {
    constructor() {
        this.rules = {
            required: (value) => value !== null && value !== undefined && value.toString().trim() !== '',
            email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
            numeric: (value) => !isNaN(value) && !isNaN(parseFloat(value)),
            positive: (value) => parseFloat(value) > 0,
            minLength: (value, min) => value.length >= min,
            maxLength: (value, max) => value.length <= max,
        };
    }

    validateField(field, rules) {
        const value = field.value;
        const errors = [];

        for (const rule of rules) {
            const { type, value: ruleValue, message } = rule;
            
            if (type === 'required' && !this.rules.required(value)) {
                errors.push(message || 'Este campo es requerido');
            } else if (value && type === 'email' && !this.rules.email(value)) {
                errors.push(message || 'Formato de email inválido');
            } else if (value && type === 'numeric' && !this.rules.numeric(value)) {
                errors.push(message || 'Debe ser un número válido');
            } else if (value && type === 'positive' && !this.rules.positive(value)) {
                errors.push(message || 'Debe ser un número positivo');
            } else if (value && type === 'minLength' && !this.rules.minLength(value, ruleValue)) {
                errors.push(message || `Mínimo ${ruleValue} caracteres`);
            } else if (value && type === 'maxLength' && !this.rules.maxLength(value, ruleValue)) {
                errors.push(message || `Máximo ${ruleValue} caracteres`);
            }
        }

        return errors;
    }

    showFieldError(field, errors) {
        // Remover error previo
        this.removeFieldError(field);

        if (errors.length > 0) {
            field.classList.add('is-invalid');
            
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.innerHTML = errors.join('<br>');
            
            field.parentNode.appendChild(errorDiv);
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    }

    removeFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    validateForm(form, validationRules) {
        let isValid = true;
        
        for (const [fieldName, rules] of Object.entries(validationRules)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const errors = this.validateField(field, rules);
                this.showFieldError(field, errors);
                
                if (errors.length > 0) {
                    isValid = false;
                }
            }
        }
        
        return isValid;
    }
}

// Clase para manejo de API con retry y manejo de errores
class APIManager {
    constructor() {
        this.toast = new ToastManager();
        this.loading = new LoadingManager();
        this.retryCount = 3;
        this.retryDelay = 1000; // 1 segundo
    }

    async request(url, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            ...options
        };

        let lastError;
        
        for (let attempt = 1; attempt <= this.retryCount; attempt++) {
            try {
                const response = await fetch(url, config);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                return data;
                
            } catch (error) {
                lastError = error;
                
                if (attempt < this.retryCount) {
                    // Mostrar retry toast solo en el primer intento
                    if (attempt === 1) {
                        this.toast.show('Reintentando conexión...', 'warning', 2000);
                    }
                    
                    // Esperar antes del siguiente intento
                    await this.sleep(this.retryDelay * attempt);
                }
            }
        }
        
        // Si llegamos aquí, todos los intentos fallaron
        throw lastError;
    }

    async getJSON(url, loadingElement = null, loadingMessage = 'Cargando...') {
        if (loadingElement) {
            this.loading.show(loadingElement, loadingMessage);
        }

        try {
            const data = await this.request(url);
            return data;
        } finally {
            if (loadingElement) {
                this.loading.hide(loadingElement);
            }
        }
    }

    async postJSON(url, data, loadingElement = null) {
        if (loadingElement) {
            this.loading.show(loadingElement, 'Enviando...');
        }

        try {
            const result = await this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
            
            this.toast.show('Datos enviados correctamente', 'success');
            return result;
        } finally {
            if (loadingElement) {
                this.loading.hide(loadingElement);
            }
        }
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Instancias globales
const toastManager = new ToastManager();
const loadingManager = new LoadingManager();
const formValidator = new FormValidator();
const apiManager = new APIManager();

// Instancias de UX mejoradas
let pwaManager, themeManager, sidebarManager, globalSearch;

// ========================================
// FUNCIONES ESPECÍFICAS DE LA APLICACIÓN
// ========================================

// Actualizar comitentes con mejoras UX
async function updateComitentes(brokerId, loadingElement = 'Comitente') {
    const comitenteSelect = document.getElementById('Comitente');
    
    if (!comitenteSelect) {
        console.error('Elemento Comitente no encontrado');
        return;
    }

    // Limpiar selección
    comitenteSelect.innerHTML = '<option value="">Seleccionar...</option>';
    
    if (!brokerId) return;

    try {
        // Mostrar loading
        loadingManager.show(loadingElement, 'Cargando comitentes...');
        
        const data = await apiManager.getJSON(`/get_comitentes/${brokerId}`);
        
        if (data.comitentes && data.comitentes.length > 0) {
            data.comitentes.forEach(comitente => {
                const option = document.createElement('option');
                option.value = comitente.Id_Comitente;
                option.textContent = comitente.Titular;
                comitenteSelect.appendChild(option);
            });
        } else {
            comitenteSelect.innerHTML = '<option value="">No hay comitentes disponibles</option>';
            toastManager.show('No se encontraron comitentes para este broker', 'warning');
        }
        
    } catch (error) {
        console.error('Error cargando comitentes:', error);
        comitenteSelect.innerHTML = '<option value="">Error al cargar comitentes</option>';
        toastManager.show('Error al cargar comitentes: ' + error.message, 'error');
    } finally {
        loadingManager.hide(loadingElement);
    }
}

// Cargar tickers con validación
async function updateTickers(instrumentoId, loadingElement = 'tickernombre') {
    const tickerSelect = document.getElementById('tickernombre');
    const descripcionInput = document.getElementById('descripcionTicker');
    
    if (!tickerSelect) return;

    // Limpiar campos
    tickerSelect.innerHTML = '<option value="">Seleccionar...</option>';
    if (descripcionInput) descripcionInput.value = '';
    
    if (!instrumentoId) return;

    try {
        loadingManager.show(loadingElement, 'Cargando tickers...');
        
        const data = await apiManager.getJSON(`/get_tickers/${instrumentoId}`);
        
        if (data.tickers && data.tickers.length > 0) {
            data.tickers.forEach(ticker => {
                const option = document.createElement('option');
                option.value = ticker.Id_Ticker;
                option.textContent = `${ticker.Nombre_Ticker} - ${ticker.Descripcion}`;
                option.setAttribute('data-descripcion', ticker.Descripcion);
                tickerSelect.appendChild(option);
            });
        } else {
            tickerSelect.innerHTML = '<option value="">No hay tickers disponibles</option>';
            toastManager.show('No se encontraron tickers para este instrumento', 'warning');
        }
        
    } catch (error) {
        console.error('Error cargando tickers:', error);
        tickerSelect.innerHTML = '<option value="">Error al cargar tickers</option>';
        toastManager.show('Error al cargar tickers: ' + error.message, 'error');
    } finally {
        loadingManager.hide(loadingElement);
    }
}

// Cargar comisión del broker
async function loadBrokerCommission(brokerId) {
    const comisionInput = document.getElementById('comisionBroker');
    if (!comisionInput || !brokerId) return;

    try {
        const data = await apiManager.getJSON(`/get_comision_broker/${brokerId}`);
        
        if (data.comision) {
            comisionInput.value = data.comision;
        } else {
            comisionInput.value = '';
        }
        
    } catch (error) {
        console.error('Error cargando comisión:', error);
        comisionInput.value = 'Error al cargar comisión';
        toastManager.show('Error al cargar comisión del broker', 'error');
    }
}

// Actualizar descripción del ticker
function updateTickerDescription() {
    const tickerSelect = document.getElementById('tickernombre');
    const descripcionInput = document.getElementById('descripcionTicker');
    
    if (!tickerSelect || !descripcionInput) return;

    const selectedOption = tickerSelect.options[tickerSelect.selectedIndex];
    if (selectedOption && selectedOption.hasAttribute('data-descripcion')) {
        const descripcion = selectedOption.getAttribute('data-descripcion');
        descripcionInput.value = descripcion;
    } else {
        descripcionInput.value = '';
    }
}

// Validación de formulario de compra con reglas avanzadas
function validateCompraForm() {
    const form = document.querySelector('form[action*="registrar_compra"]');
    if (!form) return false;

    const validationRules = {
        'Id_Broker': [
            { type: 'required', message: 'Debe seleccionar un broker' }
        ],
        'Id_Comitente': [
            { type: 'required', message: 'Debe seleccionar un comitente' }
        ],
        'Id_InstrumentoFinanciero': [
            { type: 'required', message: 'Debe seleccionar un instrumento' }
        ],
        'Id_Ticker': [
            { type: 'required', message: 'Debe seleccionar un ticker' }
        ],
        'precioDolarMEPCompra': [
            { type: 'required', message: 'El precio del dólar MEP es requerido' },
            { type: 'numeric', message: 'Debe ser un número válido' },
            { type: 'positive', message: 'Debe ser mayor a 0' }
        ],
        'precioCompra': [
            { type: 'required', message: 'El precio de compra es requerido' },
            { type: 'numeric', message: 'Debe ser un número válido' },
            { type: 'positive', message: 'Debe ser mayor a 0' }
        ],
        'cantidadCompra': [
            { type: 'required', message: 'La cantidad es requerida' },
            { type: 'numeric', message: 'Debe ser un número válido' },
            { type: 'positive', message: 'Debe ser mayor a 0' }
        ],
        'fechaHoraCompra': [
            { type: 'required', message: 'La fecha y hora es requerida' }
        ]
    };

    const isValid = formValidator.validateForm(form, validationRules);
    
    if (!isValid) {
        toastManager.show('Por favor, corrija los errores en el formulario', 'error');
        // Enfocar el primer campo con error
        const firstError = form.querySelector('.is-invalid');
        if (firstError) {
            firstError.focus();
        }
    }
    
    return isValid;
}

// Calcular totales con validación mejorada
function calcularTotales() {
    const dolarInput = document.getElementById('precioDolarMEPCompra');
    const precioInput = document.getElementById('precioCompra');
    const cantidadInput = document.getElementById('cantidadCompra');
    const totalPesosInput = document.getElementById('totalPesosCompra');
    const totalDolaresInput = document.getElementById('totalDolaresCompra');
    
    if (!dolarInput || !precioInput || !cantidadInput || !totalPesosInput || !totalDolaresInput) {
        return;
    }

    const dolar = parseFloat(dolarInput.value) || 0;
    const precio = parseFloat(precioInput.value) || 0;
    const cantidad = parseFloat(cantidadInput.value) || 0;

    if (dolar > 0 && precio >= 0 && cantidad >= 0) {
        const totalPesos = precio * cantidad;
        const totalDolares = totalPesos / dolar;
        
        totalPesosInput.value = totalPesos.toLocaleString('es-AR', { minimumFractionDigits: 2 });
        totalDolaresInput.value = totalDolares.toLocaleString('es-AR', { minimumFractionDigits: 3 });
        
        // Validar que los valores sean razonables
        if (totalPesos > 10000000) {
            toastManager.show('El monto total es muy alto. Verifique los valores ingresados.', 'warning', 3000);
        }
    }
}

// Función para formatear números en inputs
function setupNumberFormatting() {
    const numberInputs = document.querySelectorAll('input[type="number"], input[type="text"]');
    
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.type === 'number' && this.value) {
                const value = parseFloat(this.value);
                if (!isNaN(value)) {
                    if (this.id.includes('Compra') && !this.id.includes('Dolar')) {
                        this.value = value.toLocaleString('es-AR', { minimumFractionDigits: 2 });
                    } else if (this.id.includes('cantidad')) {
                        this.value = value.toLocaleString('es-AR');
                    }
                }
            }
        });
        
        input.addEventListener('focus', function() {
            if (this.type === 'text' && this.value) {
                // Remover formato para edición
                this.value = this.value.replace(/[^\d.-]/g, '');
            }
        });
    });
}

// Configurar eventos de teclado para mejor UX
function setupKeyboardNavigation() {
    // Navegación con Enter en selects
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.classList.contains('form-select')) {
            e.preventDefault();
            const nextElement = e.target.closest('.row').nextElementSibling?.querySelector('input, select');
            if (nextElement) {
                nextElement.focus();
            }
        }
    });
    
    // Atajo Ctrl+Enter para enviar formularios
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter' && e.target.closest('form')) {
            e.preventDefault();
            const submitBtn = e.target.closest('form').querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.click();
            }
        }
    });
}

// Función para mejorar accesibilidad
function improveAccessibility() {
    // Agregar aria-labels dinámicamente
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
            const label = document.querySelector(`label[for="${input.id}"]`);
            if (label && label.textContent.trim()) {
                input.setAttribute('aria-label', label.textContent.trim());
            }
        }
    });
    
    // Mejorar navegación con teclado
    const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');
    focusableElements.forEach((element, index) => {
        if (!element.getAttribute('tabindex')) {
            element.setAttribute('tabindex', '0');
        }
    });
}

// ========================================
// PWA Y SERVICE WORKER
// ========================================

// Clase para manejar PWA
class PWAManager {
    constructor() {
        this.swRegistration = null;
        this.isOnline = navigator.onLine;
        this.updateAvailable = false;
    }

    async init() {
        if (!CONFIG.PWA_ENABLED) {
            console.log('⚠️ PWA no soportado en este navegador');
            return;
        }

        try {
            // Registrar Service Worker
            this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('✅ Service Worker registrado:', this.swRegistration);

            // Escuchar actualizaciones
            this.swRegistration.addEventListener('updatefound', () => {
                const newWorker = this.swRegistration.installing;
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.updateAvailable = true;
                        this.showUpdateToast();
                    }
                });
            });

            // Escuchar cambios de conectividad
            window.addEventListener('online', () => this.handleOnline());
            window.addEventListener('offline', () => this.handleOffline());

            // Verificar si está instalado
            this.checkInstallPrompt();

        } catch (error) {
            console.error('❌ Error registrando Service Worker:', error);
        }
    }

    showUpdateToast() {
        toastManager.show(
            'Nueva versión disponible. <button class="btn btn-sm btn-outline-primary ms-2" onclick="window.location.reload()">Actualizar</button>',
            'info',
            10000
        );
    }

    handleOnline() {
        this.isOnline = true;
        toastManager.show('Conexión restaurada', 'success', 2000);
        document.body.classList.remove('offline');
    }

    handleOffline() {
        this.isOnline = false;
        toastManager.show('Sin conexión. Trabajando offline.', 'warning', 3000);
        document.body.classList.add('offline');
    }

    async checkInstallPrompt() {
        // Detectar si la app puede ser instalada
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallBanner();
        });
    }

    showInstallBanner() {
        const banner = document.createElement('div');
        banner.className = 'install-banner bg-primary text-white p-3 position-fixed bottom-0 start-0 end-0';
        banner.style.zIndex = '9999';
        banner.innerHTML = `
            <div class="container">
                <div class="row align-items-center">
                    <div class="col">
                        <i class="fas fa-download me-2"></i>
                        <strong>Instalar Cartera Financiera</strong>
                        <small class="d-block">Accede más rápido y funciona offline</small>
                    </div>
                    <div class="col-auto">
                        <button class="btn btn-light btn-sm me-2" id="install-btn">Instalar</button>
                        <button class="btn btn-outline-light btn-sm" id="dismiss-btn">Cerrar</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(banner);
        
        document.getElementById('install-btn').addEventListener('click', () => this.installApp());
        document.getElementById('dismiss-btn').addEventListener('click', () => banner.remove());
    }

    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                toastManager.show('Aplicación instalada correctamente', 'success');
            }
            
            this.deferredPrompt = null;
            document.querySelector('.install-banner')?.remove();
        }
    }
}

// Clase para manejar tema oscuro
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem(CONFIG.THEME_KEY) || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.createToggleButton();
        this.setupAutoTheme();
    }

    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem(CONFIG.THEME_KEY, theme);
        
        // Actualizar meta theme-color para PWA
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#667eea');
        }
    }

    toggle() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        // Animación de transición
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
        
        toastManager.show(
            `Tema ${newTheme === 'dark' ? 'oscuro' : 'claro'} activado`,
            'info',
            2000
        );
    }

    createToggleButton() {
        // Crear botón toggle si no existe
        if (document.getElementById('theme-toggle')) return;
        
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        const toggleLi = document.createElement('li');
        toggleLi.className = 'nav-item';
        toggleLi.innerHTML = `
            <button id="theme-toggle" class="btn btn-outline-light btn-sm" title="Cambiar tema">
                <i class="fas ${this.currentTheme === 'dark' ? 'fa-sun' : 'fa-moon'}"></i>
            </button>
        `;
        
        navbar.appendChild(toggleLi);
        document.getElementById('theme-toggle').addEventListener('click', () => this.toggle());
    }

    setupAutoTheme() {
        // Detectar preferencia del sistema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            if (!localStorage.getItem(CONFIG.THEME_KEY)) {
                this.applyTheme('dark');
            }
        }
        
        // Escuchar cambios en la preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(CONFIG.THEME_KEY)) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

// Clase para manejar sidebar colapsible
class SidebarManager {
    constructor() {
        this.isCollapsed = localStorage.getItem(CONFIG.SIDEBAR_KEY) === 'true';
        this.init();
    }

    init() {
        this.applySidebarState();
        this.createToggleButton();
    }

    toggle() {
        this.isCollapsed = !this.isCollapsed;
        this.applySidebarState();
        localStorage.setItem(CONFIG.SIDEBAR_KEY, this.isCollapsed);
    }

    applySidebarState() {
        const sidebar = document.getElementById('sidebar') || document.querySelector('.sidebar');
        if (!sidebar) return;
        
        if (this.isCollapsed) {
            sidebar.classList.add('collapsed');
        } else {
            sidebar.classList.remove('collapsed');
        }
        
        // Actualizar botón toggle
        const toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.innerHTML = `<i class="fas ${this.isCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'}"></i>`;
        }
    }

    createToggleButton() {
        if (document.getElementById('sidebar-toggle')) return;
        
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        const toggleLi = document.createElement('li');
        toggleLi.className = 'nav-item';
        toggleLi.innerHTML = `
            <button id="sidebar-toggle" class="btn btn-outline-light btn-sm" title="Alternar menú">
                <i class="fas ${this.isCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'}"></i>
            </button>
        `;
        
        navbar.appendChild(toggleLi);
        document.getElementById('sidebar-toggle').addEventListener('click', () => this.toggle());
    }
}

// Clase para búsqueda global
class GlobalSearch {
    constructor() {
        this.searchIndex = [];
        this.isInitialized = false;
    }

    async init() {
        await this.buildSearchIndex();
        this.createSearchBox();
        this.setupKeyboardShortcut();
    }

    async buildSearchIndex() {
        // Construir índice de búsqueda desde las páginas disponibles
        this.searchIndex = [
            { title: 'Dashboard', url: '/dashboard', keywords: 'resumen cartera overview' },
            { title: 'Comprar', url: '/compra', keywords: 'compra purchase buy' },
            { title: 'Vender', url: '/venta', keywords: 'venta sell sale' },
            { title: 'Informes', url: '/informe', keywords: 'informes reports analysis' },
            { title: 'Dashboard Avanzado', url: '/dashboard_avanzado', keywords: 'avanzado advanced metrics analytics' },
            { title: 'Importar Datos', url: '/importar_datos', keywords: 'importar import upload' },
            { title: 'Descarga Reportes', url: '/descarga_reportes', keywords: 'descarga download export' }
        ];
        
        this.isInitialized = true;
    }

    createSearchBox() {
        if (document.getElementById('global-search')) return;
        
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        const searchLi = document.createElement('li');
        searchLi.className = 'nav-item dropdown';
        searchLi.innerHTML = `
            <div class="dropdown">
                <input type="text" id="global-search" class="form-control form-control-sm" 
                       placeholder="Buscar... (Ctrl+K)" autocomplete="off" style="width: 200px;">
                <div id="search-results" class="dropdown-menu" style="display: none; max-height: 300px; overflow-y: auto;"></div>
            </div>
        `;
        
        navbar.appendChild(searchLi);
        
        const searchInput = document.getElementById('global-search');
        const searchResults = document.getElementById('search-results');
        
        searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value, searchResults));
        searchInput.addEventListener('focus', () => {
            if (searchInput.value) this.showResults(searchResults);
        });
        
        document.addEventListener('click', (e) => {
            if (!searchLi.contains(e.target)) {
                this.hideResults(searchResults);
            }
        });
    }

    handleSearch(query, resultsContainer) {
        if (!this.isInitialized || query.length < 2) {
            this.hideResults(resultsContainer);
            return;
        }
        
        const results = this.searchIndex.filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.keywords.toLowerCase().includes(query.toLowerCase())
        );
        
        this.displayResults(results, query, resultsContainer);
    }

    displayResults(results, query, container) {
        if (results.length === 0) {
            container.innerHTML = '<div class="dropdown-item text-muted">No se encontraron resultados</div>';
        } else {
            container.innerHTML = results.map(result => `
                <a class="dropdown-item" href="${result.url}">
                    <i class="fas fa-link me-2"></i>${result.title}
                </a>
            `).join('');
        }
        
        this.showResults(container);
    }

    showResults(container) {
        container.style.display = 'block';
    }

    hideResults(container) {
        container.style.display = 'none';
    }

    setupKeyboardShortcut() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }
}

// ========================================
// INICIALIZACIÓN Y EVENT LISTENERS
// ========================================

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', async function() {
    // Inicializar PWA y UX Managers
    try {
        pwaManager = new PWAManager();
        themeManager = new ThemeManager();
        sidebarManager = new SidebarManager();
        globalSearch = new GlobalSearch();
        
        // Inicializar PWA
        await pwaManager.init();
        
        // Inicializar búsqueda global
        await globalSearch.init();
        
        console.log('🚀 Cartera Financiera - UX Managers inicializados');
    } catch (error) {
        console.error('Error inicializando UX managers:', error);
    }

    // Configurar eventos para formulario de compra
    const brokerSelect = document.getElementById('Broker');
    if (brokerSelect) {
        brokerSelect.addEventListener('change', function() {
            updateComitentes(this.value);
            loadBrokerCommission(this.value);
        });
    }

    const instrumentoSelect = document.getElementById('tipoInstrumento');
    if (instrumentoSelect) {
        instrumentoSelect.addEventListener('change', function() {
            updateTickers(this.value);
        });
    }

    const tickerSelect = document.getElementById('tickernombre');
    if (tickerSelect) {
        tickerSelect.addEventListener('change', updateTickerDescription);
    }

    // Eventos para cálculo de totales
    ['precioDolarMEPCompra', 'precioCompra', 'cantidadCompra'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', calcularTotales);
            element.addEventListener('blur', calcularTotales);
        }
    });

    // Validación de formulario
    const compraForm = document.querySelector('form[action*="registrar_compra"]');
    if (compraForm) {
        compraForm.addEventListener('submit', function(e) {
            if (!validateCompraForm()) {
                e.preventDefault();
                return false;
            }
            
            // Mostrar indicador de carga en el botón submit
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';
                submitBtn.disabled = true;
                
                // Restaurar después de un tiempo (como fallback)
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    }

    // Configurar mejoras UX
    setupNumberFormatting();
    setupKeyboardNavigation();
    improveAccessibility();
    
    // Lazy loading para imágenes
    setupLazyLoading();
    
    // Touch gestures para móviles
    setupTouchGestures();
    
    // Mostrar notificación de bienvenida en formularios
    if (compraForm) {
        setTimeout(() => {
            toastManager.show('Formulario cargado correctamente. Use Ctrl+Enter para enviar rápidamente.', 'info', 4000);
        }, 1000);
    }
});

// ========================================
// UTILIDADES GLOBALES
// ========================================

// Función global para mostrar errores
window.showError = function(message) {
    toastManager.show(message, 'error');
};

// Función global para mostrar éxito
window.showSuccess = function(message) {
    toastManager.show(message, 'success');
};

// Función global para mostrar advertencias
window.showWarning = function(message) {
    toastManager.show(message, 'warning');
};

// ========================================
// FUNCIONES ADICIONALES DE UX
// ========================================

// Lazy loading para imágenes y componentes
function setupLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// Touch gestures para móviles
function setupTouchGestures() {
    let startX, startY, startTime;
    
    document.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        startTime = Date.now();
    });
    
    document.addEventListener('touchend', (e) => {
        if (!startX || !startY) return;
        
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        const endTime = Date.now();
        
        const diffX = startX - endX;
        const diffY = startY - endY;
        const diffTime = endTime - startTime;
        
        // Verificar que sea un swipe rápido
        if (diffTime > 300) return;
        
        const absX = Math.abs(diffX);
        const absY = Math.abs(diffY);
        
        // Swipe left/right para navegación
        if (absX > absY && absX > 50) {
            if (diffX > 0) {
                // Swipe izquierda - siguiente elemento
                handleSwipeLeft();
            } else {
                // Swipe derecha - elemento anterior
                handleSwipeRight();
            }
        }
        
        startX = startY = null;
    });
}

function handleSwipeLeft() {
    // Navegar a la siguiente sección o elemento
    const currentSection = getCurrentSection();
    if (currentSection) {
        const nextSection = currentSection.nextElementSibling;
        if (nextSection && nextSection.classList.contains('section')) {
            nextSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

function handleSwipeRight() {
    // Navegar a la sección anterior
    const currentSection = getCurrentSection();
    if (currentSection) {
        const prevSection = currentSection.previousElementSibling;
        if (prevSection && prevSection.classList.contains('section')) {
            prevSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

function getCurrentSection() {
    const sections = document.querySelectorAll('.section');
    const scrollPosition = window.scrollY + window.innerHeight / 2;
    
    for (let section of sections) {
        const rect = section.getBoundingClientRect();
        const sectionTop = rect.top + window.scrollY;
        const sectionBottom = sectionTop + rect.height;
        
        if (scrollPosition >= sectionTop && scrollPosition <= sectionBottom) {
            return section;
        }
    }
    return null;
}

// Breadcrumbs dinámicos
function updateBreadcrumbs() {
    const breadcrumbsContainer = document.getElementById('breadcrumbs');
    if (!breadcrumbsContainer) return;
    
    const path = window.location.pathname;
    const breadcrumbs = [
        { name: 'Inicio', url: '/' },
    ];
    
    // Agregar breadcrumbs según la ruta actual
    if (path.includes('/dashboard')) {
        breadcrumbs.push({ name: 'Dashboard', url: '/dashboard' });
        if (path.includes('/dashboard_avanzado')) {
            breadcrumbs.push({ name: 'Dashboard Avanzado', url: '/dashboard_avanzado' });
        }
    } else if (path.includes('/compra')) {
        breadcrumbs.push({ name: 'Comprar', url: '/compra' });
    } else if (path.includes('/venta')) {
        breadcrumbs.push({ name: 'Vender', url: '/venta' });
    } else if (path.includes('/informe')) {
        breadcrumbs.push({ name: 'Informes', url: '/informe' });
    } else if (path.includes('/importar')) {
        breadcrumbs.push({ name: 'Importar', url: '/importar_datos' });
    }
    
    // Renderizar breadcrumbs
    breadcrumbsContainer.innerHTML = breadcrumbs.map((crumb, index) => {
        const isLast = index === breadcrumbs.length - 1;
        return `
            <li class="breadcrumb-item ${isLast ? 'active' : ''}">
                ${isLast ? crumb.name : `<a href="${crumb.url}">${crumb.name}</a>`}
            </li>
        `;
    }).join('');
}

// Función global para obtener datos con loading
window.getDataWithLoading = function(url, elementId, message) {
    return apiManager.getJSON(url, elementId, message);
};

// Exportar funciones para uso global
window.CarteraFinanciera = {
    updateComitentes,
    updateTickers,
    loadBrokerCommission,
    updateTickerDescription,
    validateCompraForm,
    calcularTotales,
    toastManager,
    loadingManager,
    formValidator,
    apiManager,
    pwaManager,
    themeManager,
    sidebarManager,
    globalSearch,
    updateBreadcrumbs
};

// Actualizar breadcrumbs cuando cambie la ruta
window.addEventListener('popstate', updateBreadcrumbs);
window.addEventListener('load', updateBreadcrumbs);

// Mensaje de inicialización
console.log('🚀 Cartera Financiera - JavaScript Moderno con PWA y UX avanzado cargado correctamente');
