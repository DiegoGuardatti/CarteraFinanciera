# 🌳 ESTRATEGIA DE GIT BRANCHING - CARTERA FINANCIERA

## 🎯 OBJETIVO

Establecer una estrategia de branching profesional para desarrollo organizado, colaboración eficiente y deployment seguro del proyecto Cartera Financiera.

## 📊 ESTRUCTURA DE RAMAS

### 🏗️ Ramas Principales

```
main                    # Producción - Código estable y deployado
├── develop            # Desarrollo - Integración de features
├── feature/*          # Features específicas (nueva funcionalidad)
├── bugfix/*           # Corrección de bugs
├── hotfix/*           # Hotfixes urgentes para producción
└── release/*          # Preparación de releases
```

### 📋 Ramas Actuales

```bash
# Ramas principales
main                    # ✅ Producción estable
develop                 # ✅ Rama de desarrollo activa

# Ramas de features (Fase 1 - Críticas)
feature/docker-implementation      # 🐳 Dockerización completa
feature/app-refactoring            # 🏗️ Refactorización app.py modular
feature/testing-system             # 🧪 Sistema de testing completo
feature/security-hardening         # 🛡️ Seguridad robusta
feature/performance-optimization   # ⚡ Optimizaciones de performance
```

## 🔄 WORKFLOW RECOMENDADO

### 1. 🌱 Inicio de Nueva Feature

```bash
# 1. Actualizar develop
git checkout develop
git pull origin develop

# 2. Crear rama para la feature
git checkout -b feature/nueva-funcionalidad

# 3. Desarrollo y commits
git add .
git commit -m "feat: agregar nueva funcionalidad"

# 4. Push de la rama
git push origin feature/nueva-funcionalidad
```

### 2. 🔀 Integración a Develop

```bash
# 1. Hacer merge a develop (localmente para testing)
git checkout develop
git merge feature/nueva-funcionalidad

# 2. Resolver conflictos si existen
# git mergetool  # Si hay conflictos

# 3. Tests finales
make test
make lint

# 4. Commit del merge
git commit -m "merge: integrar feature/nueva-funcionalidad"

# 5. Push
git push origin develop
```

### 3. 🚀 Deploy a Producción

```bash
# 1. Crear rama de release
git checkout develop
git checkout -b release/v1.0.0

# 2. Preparar release (versionado, changelog, etc.)
# ... cambios específicos del release ...

# 3. Merge a main
git checkout main
git merge release/v1.0.0
git tag v1.0.0

# 4. Merge back a develop
git checkout develop
git merge release/v1.0.0

# 5. Push todo
git push origin main
git push origin develop
git push origin --tags
```

## 📋 CONVENCIONES DE NOMBRES

### 🏷️ Prefijos de Ramas

- **`feature/`** - Nueva funcionalidad

  - `feature/docker-implementation`
  - `feature/dashboard-avanzado`
  - `feature/api-nuevas-metricas`

- **`bugfix/`** - Corrección de bugs

  - `bugfix/fix-csrf-validation`
  - `bugfix/correct-calculation-error`

- **`hotfix/`** - Hotfix urgente para producción

  - `hotfix/security-vulnerability`
  - `hotfix/critical-database-error`

- **`release/`** - Preparación de releases
  - `release/v1.0.0`
  - `release/v1.1.0-beta`

### 📝 Mensajes de Commit

Usar [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>[alcance opcional]: <descripción>

[cuerpo opcional]

[footer(s) opcional]
```

#### Tipos de Commit:

- **`feat`**: Nueva feature

  - `feat(api): agregar endpoint para TIR`
  - `feat(dashboard): implementar gráficos interactivos`

- **`fix`**: Bug fix

  - `fix(database): corregir error de conexión`
  - `fix(ui): solucionar problema de responsive`

- **`docs`**: Documentación

  - `docs(readme): actualizar instrucciones de instalación`

- **`style`**: Formateo de código

  - `style(code): formatear con black`

- **`refactor`**: Refactorización

  - `refactor(app): dividir app.py en módulos`

- **`test`**: Tests

  - `test(metrics): agregar tests para cálculo ROI`

- **`chore`**: Mantenimiento
  - `chore(deps): actualizar dependencias`

## 🎯 RAMAS POR FASE DE MEJORAS

### 🔥 Fase 1 (Críticas)

```bash
# Crear desde develop
git checkout develop
git checkout -b feature/app-refactoring          # Refactorización app.py
git checkout -b feature/testing-system           # Sistema de testing
git checkout -b feature/security-hardening       # Seguridad robusta
```

### 🔶 Fase 2 (Altas)

```bash
git checkout -b feature/performance-optimization # Performance
git checkout -b feature/ui-improvements         # UX/UI profesional
git checkout -b feature/mobile-responsive       # Responsive design
```

### 🔷 Fase 3 (Medias)

```bash
git checkout -b feature/advanced-metrics        # Métricas avanzadas
git checkout -b feature/interactive-charts      # Visualizaciones
git checkout -b feature/external-apis          # APIs externas
```

### 🔵 Fase 4 (Bajas)

```bash
git checkout -b feature/docker-implementation   # Docker
git checkout -b feature/ci-cd-pipeline         # CI/CD
git checkout -b feature/backup-system          # Backup automatizado
```

### 🟢 Fase 5 (Simples)

```bash
git checkout -b feature/themes-customization    # Temas
git checkout -b feature/mobile-app             # App móvil
git checkout -b feature/automation-ai          # Automatización IA
```

## 🛠️ COMANDOS ÚTILES

### 📊 Ver Estado de Ramas

```bash
git branch -a                    # Todas las ramas locales y remotas
git branch --merged develop      # Ramas mergeadas a develop
git log --oneline --graph --all  # Visualización completa
```

### 🧹 Limpieza de Ramas

```bash
# Eliminar rama localmente
git branch -d feature/completada

# Eliminar rama remotamente
git push origin --delete feature/completada

# Limpiar referencias locales
git remote prune origin
```

### 🔄 Sincronización

```bash
# Actualizar develop con cambios remotos
git checkout develop
git pull origin develop

# Rebase de feature sobre develop actualizada
git checkout feature/mi-feature
git rebase develop
```

## 🏷️ TAGS Y VERSIONES

### Crear Tags

```bash
# Tag simple
git tag v1.0.0

# Tag con anotación
git tag -a v1.0.0 -m "Release version 1.0.0"

# Tag con firma GPG
git tag -s v1.0.0 -m "Release version 1.0.0"

# Push tags
git push origin --tags
```

### Tipos de Tags

- **`v1.0.0`** - Releases principales
- **`v1.0.0-beta`** - Betas
- **`v1.0.0-rc1`** - Release candidates
- **`v1.0.0-hotfix`** - Hotfixes

## 🚀 BENEFICIOS DE ESTA ESTRATEGIA

### ✅ Organización

- **Desarrollo paralelo**: Múltiples features simultáneas
- **Integración controlada**: Merge solo a develop
- **Deploy seguro**: Solo main a producción

### ✅ Calidad

- **Code review**: Pull requests obligatorios
- **Testing**: Cada rama se testa independientemente
- **Rollback**: Fácil reversión de cambios

### ✅ Colaboración

- **Equipos**: Múltiples desarrolladores simultáneos
- **Historial**: Rastro claro de cambios
- **Comunicación**: Naming conventions claras

### ✅ Mantenimiento

- **Hotfixes**: Ramas específicas para urgencias
- **Releases**: Preparación controlada
- **Documentación**: Estructura auto-documentada

## 🎯 PRÓXIMOS PASOS

1. **✅ Implementado**: Rama develop y ramas de features
2. **🔄 En progreso**: Trabajo en ramas específicas
3. **📋 Pendiente**: Pull requests y code review
4. **🚀 Futuro**: CI/CD automático por rama

---

**Esta estrategia garantiza desarrollo profesional, colaboración eficiente y deploys seguros para el proyecto Cartera Financiera.**
