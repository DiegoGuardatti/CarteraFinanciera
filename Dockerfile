# Dockerfile
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    mariadb-client-compat \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

# Crear directorios necesarios como root antes de cambiar a usuario app
RUN mkdir -p instance logs uploads && \
    chmod 755 instance logs uploads && \
    chown app:app instance logs uploads

USER app

# Agregar ~/.local/bin al PATH para que los paquetes instalados con --user sean accesibles
ENV PATH=/home/app/.local/bin:$PATH

# Copiar requirements y instalar dependencias Python
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar código de la aplicación
COPY --chown=app:app . .

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/dashboard/summary || exit 1

# Script de entrada
COPY --chown=app:app scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chown=app:app scripts/wait-for-db.sh /usr/local/bin/wait-for-db.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/wait-for-db.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
# OPTIMIZADO: Aumentado timeout a 120s y reducido workers a 2 para evitar problemas de memoria
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--graceful-timeout", "30", "--max-requests", "1000", "--max-requests-jitter", "50", "app:app"]