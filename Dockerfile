# Dockerfile
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app
USER app

# Copiar requirements y instalar dependencias Python
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar código de la aplicación
COPY --chown=app:app . .

# Crear directorios necesarios
RUN mkdir -p instance logs uploads
RUN chmod 755 instance logs uploads

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/dashboard/summary || exit 1

# Script de entrada
COPY --chown=app:app scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]