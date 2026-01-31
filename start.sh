#!/bin/bash

# Script de inicio rápido para el Sistema de Reservas IES
# Este script automatiza la configuración inicial del proyecto

set -e

echo "🚀 Iniciando Sistema de Reservas IES..."
echo "======================================"

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor, instala Docker primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    exit 1
fi

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde plantilla..."
    cp env.example .env
    echo "⚠️  Por favor, edita el archivo .env con tus credenciales de Supabase antes de continuar."
    echo "   - SUPABASE_URL: URL de tu proyecto Supabase"
    echo "   - SUPABASE_KEY: Clave anónima de tu proyecto Supabase"
    echo "   - DATABASE_URL: URL de conexión a la base de datos"
    echo ""
    read -p "¿Has configurado el archivo .env? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Por favor, configura el archivo .env y ejecuta este script nuevamente."
        exit 1
    fi
fi

# Construir la imagen Docker
echo "🔨 Construyendo imagen Docker..."
docker compose build

# Ejecutar la aplicación
echo "🚀 Iniciando la aplicación..."
docker compose up -d

# Esperar a que la aplicación esté lista
echo "⏳ Esperando a que la aplicación esté lista..."
sleep 10

# Verificar el estado de la aplicación
if docker compose ps | grep -q "Up"; then
    echo "✅ Aplicación iniciada correctamente!"
    echo ""
    echo "🌐 URLs disponibles:"
    echo "   - Aplicación web: http://localhost:8000"
    echo "   - Documentación API: http://localhost:8000/api/docs"
    echo "   - ReDoc: http://localhost:8000/api/redoc"
    echo ""
    echo "🔑 Credenciales por defecto:"
    echo "   - Administrador: admin / admin123"
    echo "   - Profesor 1: profesor1 / profesor123"
    echo "   - Profesor 2: profesor2 / profesor123"
    echo "   - Profesor 3: profesor3 / profesor123"
    echo ""
    echo "📊 Para inicializar la base de datos con datos de muestra:"
    echo "   docker compose exec web python -m app.utils.init_db"
    echo ""
    echo "📋 Para ver los logs:"
    echo "   docker compose logs -f"
    echo ""
    echo "🛑 Para detener la aplicación:"
    echo "   docker compose down"
else
    echo "❌ Error al iniciar la aplicación. Revisa los logs:"
    docker compose logs
    exit 1
fi

