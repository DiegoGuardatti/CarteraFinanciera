# 📊 Cartera Financiera - Sistema de Gestión de Inversiones

[![GitHub](https://img.shields.io/badge/GitHub-repository-blue)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Sistema profesional para gestión de carteras financieras con métricas avanzadas, análisis de riesgo y reportes ejecutivos.

## 🎯 Características Principales

### 💼 Métricas Financieras Institucionales

- ✅ **ROI** (Return on Investment) individual y por cartera
- ✅ **TIR** (Tasa Interna de Retorno) con método Newton-Raphson
- ✅ **Sharpe Ratio** para análisis riesgo-retorno
- ✅ **Value at Risk (VaR)** para gestión de riesgo
- ✅ **Beta y Alpha** para análisis de mercado
- ✅ **Maximum Drawdown** para evaluación de pérdidas
- ✅ **Matriz de correlación** entre activos
- ✅ **Backtesting** de estrategias de inversión

### 📈 Dashboard Ejecutivo

- ✅ **Dashboard básico** con KPIs principales
- ✅ **Dashboard avanzado** con análisis profesional
- ✅ **Visualizaciones interactivas** con Plotly.js
- ✅ **Métricas en tiempo real** con cache inteligente
- ✅ **Top/Bottom performers** automáticos

### 🔧 APIs RESTful Completas

- ✅ **15+ endpoints** para métricas financieras
- ✅ **Documentación automática** con Flasgger
- ✅ **Caching con Redis** para performance
- ✅ **Rate limiting** para seguridad
- ✅ **Validación robusta** de datos

### 📊 Sistema de Reportes

- ✅ **Exportación CSV** con filtros avanzados
- ✅ **Reportes Excel** multi-hoja profesionales
- ✅ **PDFs ejecutivos** con branding corporativo
- ✅ **Reportes automatizados** programables

## 🚀 Inicio Rápido

### Prerrequisitos

```bash
Python 3.11+
MySQL 8.0+ (opcional, SQLite por defecto)
Redis (opcional, para cache)
```

### Instalación en 1 Comando

```bash
# Clonar e instalar
git clone <repository-url>
cd Cartera-Financiera
make install
make run
```

### Comandos de Desarrollo

```bash
make help          # Ver todos los comandos
make install       # Instalar dependencias
make run           # Ejecutar aplicación
make test          # Ejecutar tests
make lint          # Verificar código
make format        # Formatear código
make clean         # Limpiar archivos temporales
make backup        # Backup de base de datos
```

## 📱 URLs de la Aplicación

Una vez ejecutando la aplicación en `http://localhost:5000`:

| Ruta                  | Descripción                           |
| --------------------- | ------------------------------------- |
| `/`                   | Página principal                      |
| `/dashboard`          | Dashboard ejecutivo básico            |
| `/dashboard_avanzado` | Dashboard con análisis profesional ⭐ |
| `/compra`             | Registrar nueva compra                |
| `/venta`              | Registrar nueva venta                 |
| `/informe`            | Informes con filtros avanzados        |
| `/apidocs`            | Documentación API interactiva         |
| `/descarga_reportes`  | Sistema de reportes                   |

## 🔌 APIs Disponibles

### Métricas Básicas

```bash
GET /api/dashboard/summary      # Resumen ejecutivo completo
GET /api/metrics/portfolio      # ROI de cartera
GET /api/metrics/roi/{id}       # ROI de activo específico
GET /api/metrics/sharpe/{id}    # Sharpe Ratio
GET /api/metrics/var/{id}       # Value at Risk
```

### Métricas Avanzadas

```bash
GET /api/advanced/summary       # Resumen métricas avanzadas
GET /api/metrics/tir/{id}       # TIR con Newton-Raphson
GET /api/metrics/beta/{id}      # Beta y correlación
GET /api/metrics/alpha/{id}     # Alpha ajustado
GET /api/metrics/correlation-matrix  # Matriz correlación
GET /api/metrics/backtesting    # Backtesting estrategias
```

### Reportes

```bash
GET /api/reports/activos-csv    # Exportar CSV
GET /api/reports/activos-excel  # Exportar Excel
GET /api/reports/ejecutivo-pdf  # PDF ejecutivo
GET /api/reports/detalle-pdf    # PDF detallado
```

## 📋 Documentación del Proyecto

### Documentos Principales

- 📋 **[MEJORAS_UNIFICADAS_FASES.md](MEJORAS_UNIFICADAS_FASES.md)** - Roadmap completo de mejoras organizadas por prioridad
- 🐳 **[DOCKER_GIT_IMPLEMENTACION.md](DOCKER_GIT_IMPLEMENTACION.md)** - Plan de Dockerización y Git
- 📊 **[README_MINERIA.md](README_MINERIA.md)** - Sistema de importación de datos
- 🗂️ **[ARCHIVOS_DUPLICADOS_ELIMINAR.md](ARCHIVOS_DUPLICADOS_ELIMINAR.md)** - Historial de limpieza

### Documentos de Estado

- ✅ **[PROBLEMAS_RESUELTOS_FINAL.md](PROBLEMAS_RESUELTOS_FINAL.md)** - Problemas técnicos resueltos
- 📈 **[RESUMEN_FASE_2_3_COMPLETADA.md](RESUMEN_FASE_2_3_COMPLETADA.md)** - Progreso completado
- 🔄 **[RESUMEN_FASE_4_PROGRESO.md](RESUMEN_FASE_4_PROGRESO.md)** - Estado actual

## 🏗️ Arquitectura del Proyecto

```
CarteraFinanciera/
├── 📄 app.py                    # Aplicación Flask principal
├── 📄 config.py                 # Configuración por entornos
├── 📄 modelo.py                 # Modelos SQLAlchemy
├── 📄 calculos_metricas.py      # Métricas financieras básicas
├── 📄 metricas_avanzadas.py     # Métricas institucionales
├── 📄 requirements.txt          # Dependencias Python
├── 📄 Makefile                  # Comandos de desarrollo
├── 📄 .gitignore               # Archivos excluidos de Git
├── 📁 templates/               # Plantillas HTML
│   ├── index.html
│   ├── dashboard.html
│   ├── dashboard_avanzado.html
│   ├── compra.html
│   ├── venta.html
│   └── informe.html
├── 📁 static/                  # Archivos estáticos
│   ├── estilos.css
│   └── funciones.js
├── 📁 utils/                   # Utilidades
│   ├── csv_export.py
│   ├── excel_export.py
│   ├── pdf_export.py
│   └── cache_config.py
├── 📁 migrations/              # Migraciones Alembic
├── 📁 instance/                # Base de datos SQLite
├── 📁 logs/                    # Logs del sistema
└── 📁 backup/                  # Backups automáticos
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Copiar template
cp .env.template .env

# Editar configuración
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=sqlite:///instance/cartera.db
REDIS_URL=redis://localhost:6379/0
```

### Base de Datos

```bash
# SQLite (desarrollo) - por defecto
DATABASE_URL=sqlite:///instance/cartera.db

# MySQL (producción)
DATABASE_URL=mysql+pymysql://user:pass@localhost/cartera
```

## 🧪 Testing y Calidad

### Ejecutar Tests

```bash
make test              # Tests con coverage
pytest -v              # Tests detallados
pytest --cov=html      # Reporte HTML coverage
```

### Quality Checks

```bash
make lint              # Verificar estilo (flake8)
make format            # Formatear código (black)
make security          # Verificar seguridad (bandit)
```

## 📦 Docker (Próximamente)

```bash
# Desarrollo con Docker
docker-compose -f docker-compose.dev.yml up -d

# Producción con Docker
docker-compose up -d

# Ver logs
docker-compose logs -f app
```

## 🔄 Control de Versiones

### Git Workflow

```bash
git status             # Ver estado
git add .             # Agregar cambios
git commit -m "mensaje"  # Commit (ejecuta hooks automáticamente)
git push              # Push (ejecuta tests automáticamente)
```

### Hooks Configurados

- ✅ **pre-commit**: Formatea código, verifica estilo, ejecuta tests básicos
- ✅ **pre-push**: Ejecuta suite completa de tests, verifica coverage

## 📊 Métricas del Proyecto

- **Líneas de código**: ~2,000+ Python
- **APIs implementadas**: 15+ endpoints
- **Métricas financieras**: 10+ cálculos avanzados
- **Templates HTML**: 10+ páginas
- **Cobertura de código**: >80% (objetivo)
- **Tests unitarios**: En implementación

## 🎯 Roadmap de Mejoras

Ver **[MEJORAS_UNIFICADAS_FASES.md](MEJORAS_UNIFICADAS_FASES.md)** para el roadmap completo organizado en 5 fases:

1. **🔥 Fase 1 (Críticas)**: Refactorización, testing, seguridad
2. **🔶 Fase 2 (Altas)**: Performance, UX/UI profesional
3. **🔷 Fase 3 (Medias)**: Métricas avanzadas, visualizaciones
4. **🔵 Fase 4 (Bajas)**: Docker, CI/CD, backup automatizado
5. **🟢 Fase 5 (Simples)**: Temas, mobile apps, automatización

## 🤝 Contribuir

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**Desarrollado para gestión profesional de carteras financieras**

---

⭐ **Si este proyecto te resulta útil, no olvides darle una estrella en GitHub!** ⭐
