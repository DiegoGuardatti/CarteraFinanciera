# Sistema de Testing - Cartera Financiera

## Descripción General

Este documento describe el sistema completo de testing implementado para la aplicación Cartera Financiera. El sistema está diseñado para garantizar la calidad del código, prevenir regresiones y asegurar la seguridad de la aplicación.

## Arquitectura del Sistema de Testing

### Estructura de Directorios

```
tests/
├── conftest.py              # Configuración global de pytest
├── pytest.ini              # Configuración de pytest
├── README_TESTING.md        # Este archivo
├── unit/                    # Tests unitarios
│   ├── test_config.py       # Tests de configuración
│   ├── test_main_routes.py  # Tests de rutas principales
│   └── test_models.py       # Tests de modelos de DB
├── integration/             # Tests de integración
│   └── test_workflow_integration.py # Tests de flujos completos
├── security/                # Tests de seguridad
│   └── test_security.py     # Tests de seguridad
├── database/                # Tests de base de datos
│   └── test_database.py     # Tests de DB (futuro)
└── api/                     # Tests de API
    └── test_api_endpoints.py # Tests de API (futuro)
```

### Categorías de Tests

#### 1. Tests Unitarios (`tests/unit/`)

- **Objetivo**: Verificar funcionalidades individuales
- **Alcance**: Componentes aislados (configuración, rutas, modelos)
- **Ejecución**: Rápi

#### 2. Tests de Integración (`tests/integration/`)

- **Objetivo**: Verificar interacción entre componentes
- **Alcance**: Flujos completos de trabajo
- **Ejecución**: Moderada

#### 3. Tests de Seguridad (`tests/security/`)

- **Objetivo**: Verificar seguridad de la aplicación
- **Alcance**: Autenticación, validación, headers, etc.
- **Ejecución**: Lenta

#### 4. Tests de Base de Datos (`tests/database/`) - Futuro

- **Objetivo**: Verificar integridad y rendimiento de DB
- **Alcance**: Queries, constraints, performance

#### 5. Tests de API (`tests/api/`) - Futuro

- **Objetivo**: Verificar endpoints de API
- **Alcance**: JSON responses, status codes, validaciones

## Instalación y Configuración

### Dependencias

Agregar a `requirements.txt` si no están presentes:

```bash
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-flask>=1.2.0
pytest-mock>=3.10.0
factory-boy>=3.2.0
faker>=18.0.0
```

### Configuración de Entorno

1. **Archivo `.env` para testing**:

```bash
# Configuración de testing
FLASK_ENV=testing
TESTING=True
DATABASE_URL=sqlite:///test_cartera.db
SECRET_KEY=test_secret_key_for_testing_only
```

2. **Variables de entorno específicas**:

- `TESTING=True`: Activa modo testing
- `DATABASE_URL`: URL de base de datos de testing
- `SECRET_KEY`: Clave secreta para tests

## Ejecución de Tests

### Comandos Básicos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests específicos por categoría
pytest tests/unit/                    # Solo unitarios
pytest tests/integration/             # Solo integración
pytest tests/security/                # Solo seguridad

# Ejecutar test específico
pytest tests/unit/test_config.py::TestConfig::test_app_creation

# Ejecutar tests por marcador
pytest -m unit                        # Tests marcados como unit
pytest -m "not integration"          # Excluir integración
pytest -m security                   # Solo seguridad
```

### Comandos Avanzados

```bash
# Con cobertura de código
pytest --cov=. --cov-report=html --cov-report=term

# Con reporte detallado
pytest --tb=long --durations=10

# Ejecutar tests en paralelo (requiere pytest-xdist)
pytest -n auto

# Solo tests que fallaron en la última ejecución
pytest --lf

# Ejecutar tests y parar en el primer fallo
pytest -x

# Verbose output
pytest -v

# Tests con fixtures detalladas
pytest --setup-show
```

### Configuración de pytest (pytest.ini)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=70
markers =
    unit: Tests unitarios
    integration: Tests de integración
    security: Tests de seguridad
    database: Tests de base de datos
    api: Tests de API
    slow: Tests lentos
    quick: Tests rápidos
```

## Fixtures y Datos de Prueba

### Fixtures Principales

#### `app`

- Crea aplicación Flask en modo testing
- Configura contexto de aplicación

#### `client`

- Cliente de testing Flask
- Simula requests HTTP

#### `database`

- Base de datos de testing con datos precargados
- Rollback automático después de cada test

#### `active_assets`

- Lista de activos en cartera para testing

#### `sold_assets`

- Lista de activos vendidos para testing

### Datos de Prueba

El fixture `database` incluye:

- 1 Broker
- 1 Comitente asociado al broker
- 1 Instrumento Financiero
- 1 Ticker asociado al instrumento
- 5 Activos en cartera
- 3 Activos vendidos

## Marcadores (Markers)

### Uso de Marcadores

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration
def test_complex_workflow():
    pass

@pytest.mark.security
def test_authentication():
    pass

@pytest.mark.slow
def test_performance():
    pass
```

### Ejecución con Marcadores

```bash
# Solo tests rápidos
pytest -m "not slow"

# Tests de seguridad e integración
pytest -m "security or integration"

# Excluir tests lentos de integración
pytest -m "integration and not slow"
```

## Mejores Prácticas

###编写 Tests

1. **Naming Convention**:

   - `test_[functionality]_[scenario]`
   - Ejemplo: `test_broker_creation_with_valid_data`

2. **Estructura AAA**:

   - **Arrange**: Configurar datos
   - **Act**: Ejecutar función
   - **Assert**: Verificar resultado

3. **Datos Aislados**:

   - No depender de tests anteriores
   - Usar fixtures para datos comunes

4. **Documentación**:
   - Docstrings descriptivos
   - Comentarios para lógica compleja

### Ejemplo de Test

```python
@pytest.mark.unit
def test_broker_creation_valid_data(app, database):
    """
    Test creación de broker con datos válidos
    """
    # Arrange
    broker_data = {
        'Nombre': 'Test Broker',
        'Comision': 0.5,
        'Asesor': 'Test Advisor'
    }

    # Act
    broker = Broker(**broker_data)
    db.session.add(broker)
    db.session.commit()

    # Assert
    saved_broker = Broker.query.filter_by(Nombre='Test Broker').first()
    assert saved_broker is not None
    assert saved_broker.Comision == 0.5
    assert saved_broker.Asesor == 'Test Advisor'
```

## Integración con CI/CD

### GitHub Actions (ejemplo)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
```

## Métricas y Reportes

### Cobertura de Código

```bash
# Generar reporte de cobertura
pytest --cov=. --cov-report=html --cov-report=term

# Ver reporte en navegador
open htmlcov/index.html
```

### Performance de Tests

```bash
# Ver tests más lentos
pytest --durations=10

# Profiling de tests
pytest --profile
```

## Solución de Problemas

### Problemas Comunes

1. **Tests fallan en aislamiento**:

   - Verificar fixtures y cleanup
   - Usar `yield` en fixtures para cleanup

2. **Base de datos compartida**:

   - Usar transacciones para rollback
   - Aislar datos de prueba

3. **Tests lentos**:

   - Usar `pytest-xdist` para paralelización
   - Marcar tests lentos con `@pytest.mark.slow`

4. **Mocks no funcionan**:
   - Verificar scope de mocks
   - Usar `pytest-mock` para mejores mocks

### Debug de Tests

```bash
# Debug con pdb
pytest --pdb

# Debug específico
pytest --pdbcls=IPython.terminal.debugger:Pdb

# Verbose output
pytest -v -s
```

## Mantenimiento

### Actualización Regular

1. **Dependencias**: Mantener pytest y plugins actualizados
2. **Datos de Prueba**: Actualizar fixtures con cambios de modelo
3. **Nuevos Tests**: Agregar tests para nuevas funcionalidades
4. **Performance**: Monitorear tiempos de ejecución

### Revisión de Tests

- Revisar cobertura mensualmente
- Eliminar tests obsoletos
- Actualizar assertions con cambios de requisitos
- Optimizar tests lentos

## Próximos Pasos

1. **Completar tests de API**:

   - Endpoints JSON
   - Validación de respuestas
   - Autenticación API

2. **Tests de rendimiento**:

   - Load testing con locust
   - Memory profiling
   - Database performance

3. **Tests de UI**:

   - Selenium para testing web
   - Tests de JavaScript
   - Responsive design testing

4. **Documentación automática**:
   - Génerar documentación desde tests
   - API documentation con pdoc
   - Coverage reports automáticos
