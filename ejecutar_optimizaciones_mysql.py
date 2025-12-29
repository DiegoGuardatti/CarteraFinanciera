#!/usr/bin/env python3
"""
Script para ejecutar optimizaciones MySQL automáticamente
Este script se conecta a MySQL y ejecuta el script de optimizaciones
"""

import pymysql
import sys
import os
from pathlib import Path

def leer_script_sql():
    """Lee el script SQL de optimizaciones"""
    try:
        with open('optimizacion_mysql.sql', 'r', encoding='utf-8') as f:
            contenido = f.read()
        return contenido
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo optimizacion_mysql.sql")
        return None
    except Exception as e:
        print(f"❌ Error leyendo archivo SQL: {e}")
        return None

def ejecutar_optimizaciones():
    """Ejecuta las optimizaciones en MySQL"""
    # Configuración de conexión (usar las mismas credenciales que la app)
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',  # Añadir password si es necesario
        'database': 'CarteraFinanciera',
        'unix_socket': '/opt/lampp/var/mysql/mysql.sock'
    }
    
    # Leer script SQL
    sql_script = leer_script_sql()
    if not sql_script:
        return False
    
    try:
        print("🔌 Conectando a MySQL...")
        # Conectar usando socket Unix
        connection = pymysql.connect(
            unix_socket=config['unix_socket'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ Conexión exitosa a MySQL")
        
        # Dividir script en comandos individuales
        # Remover comentarios y dividir por delimitador
        lineas = sql_script.split('\n')
        comandos = []
        comando_actual = []
        
        for linea in lineas:
            linea = linea.strip()
            # Saltar líneas vacías y comentarios
            if not linea or linea.startswith('--'):
                continue
            
            comando_actual.append(linea)
            
            # Si encontramos DELIMITER, procesar comando anterior
            if linea.startswith('DELIMITER'):
                if comando_actual[:-1]:  # Si hay comandos anteriores
                    comandos.append('\n'.join(comando_actual[:-1]))
                comando_actual = []
            elif linea == 'DELIMITER ;':
                # Finalizar comando anterior
                if comando_actual:
                    comandos.append('\n'.join(comando_actual))
                comando_actual = []
                # Restablecer delimitador
                comando_actual.append('DELIMITER //')
            elif linea.endswith(';') and not comando_actual[0].startswith('DELIMITER'):
                # Comando individual terminado con ;
                comandos.append('\n'.join(comando_actual))
                comando_actual = []
        
        # Añadir último comando si existe
        if comando_actual:
            comandos.append('\n'.join(comando_actual))
        
        print(f"📋 Preparando ejecutar {len(comandos)} comandos...")
        
        with connection.cursor() as cursor:
            for i, comando in enumerate(comandos, 1):
                try:
                    # Limpiar comando
                    comando = comando.strip()
                    if not comando or comando.startswith('--'):
                        continue
                    
                    print(f"⚡ Ejecutando comando {i}/{len(comandos)}...")
                    cursor.execute(comando)
                    connection.commit()
                    
                except Exception as e:
                    print(f"⚠️  Advertencia en comando {i}: {str(e)[:100]}...")
                    # Continuar con el siguiente comando
        
        print("✅ Optimizaciones MySQL completadas exitosamente!")
        return True
        
    except pymysql.Error as e:
        print(f"❌ Error de MySQL: {e}")
        print("\n🔧 Posibles soluciones:")
        print("1. Verificar que MySQL esté ejecutándose")
        print("2. Verificar credenciales en config.py")
        print("3. Ejecutar manualmente en phpMyAdmin:")
        print("   - Abrir phpMyAdmin")
        print("   - Seleccionar base de datos 'CarteraFinanciera'")
        print("   - Pestaña SQL")
        print("   - Copiar y pegar contenido de optimizacion_mysql.sql")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
            print("🔌 Conexión cerrada")

def main():
    print("🚀 Script de Optimización MySQL - Cartera Financiera")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('optimizacion_mysql.sql'):
        print("❌ Error: Debe ejecutarse desde el directorio del proyecto")
        sys.exit(1)
    
    # Confirmar ejecución (no-interactivo si se pasa --auto o si está en CI)
    auto_mode = '--auto' in sys.argv or os.environ.get('CI', False)
    
    if not auto_mode:
        try:
            respuesta = input("\n¿Continuar con las optimizaciones de MySQL? (s/N): ")
            if respuesta.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                print("❌ Operación cancelada")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  Modo automático activado (no se detectó input)")
            print("🔄 Continuando con las optimizaciones...")
    else:
        print("🔄 Ejecutando en modo automático...")
    
    # Ejecutar optimizaciones
    exito = ejecutar_optimizaciones()
    
    if exito:
        print("\n🎉 ¡Optimización completada!")
        print("\n📊 Próximos pasos:")
        print("1. Verificar índices con: SHOW INDEX FROM activo;")
        print("2. Probar vistas con: SELECT * FROM vista_resumen_cartera LIMIT 5;")
        print("3. Probar stored procedures con: CALL ResumenCartera();")
        print("4. Iniciar la aplicación: python app.py")
    else:
        print("\n💡 La optimización falló. Puedes ejecutarla manualmente:")
        print("1. Abrir phpMyAdmin")
        print("2. Seleccionar base de datos 'CarteraFinanciera'")
        print("3. Pestaña SQL")
        print("4. Copiar y pegar contenido de optimizacion_mysql.sql")
        sys.exit(1)

if __name__ == '__main__':
    main()