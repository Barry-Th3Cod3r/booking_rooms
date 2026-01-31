@echo off
REM Script de inicio rápido para el Sistema de Reservas IES (Windows)
REM Este script automatiza la configuración inicial del proyecto

echo 🚀 Iniciando Sistema de Reservas IES...
echo ======================================

REM Verificar si Docker está instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no está instalado. Por favor, instala Docker Desktop primero.
    pause
    exit /b 1
)

REM Verificar si Docker Compose está instalado
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose no está instalado. Por favor, instala Docker Compose primero.
    pause
    exit /b 1
)

REM Verificar si existe el archivo .env
if not exist .env (
    echo 📝 Creando archivo .env desde plantilla...
    copy env.example .env
    echo ⚠️  Por favor, edita el archivo .env con tus credenciales de Supabase antes de continuar.
    echo    - SUPABASE_URL: URL de tu proyecto Supabase
    echo    - SUPABASE_KEY: Clave anónima de tu proyecto Supabase
    echo    - DATABASE_URL: URL de conexión a la base de datos
    echo.
    set /p reply="¿Has configurado el archivo .env? (y/n): "
    if /i not "%reply%"=="y" (
        echo Por favor, configura el archivo .env y ejecuta este script nuevamente.
        pause
        exit /b 1
    )
)

REM Construir la imagen Docker
echo 🔨 Construyendo imagen Docker...
docker-compose build

REM Ejecutar la aplicación
echo 🚀 Iniciando la aplicación...
docker-compose up -d

REM Esperar a que la aplicación esté lista
echo ⏳ Esperando a que la aplicación esté lista...
timeout /t 10 /nobreak >nul

REM Verificar el estado de la aplicación
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Aplicación iniciada correctamente!
    echo.
    echo 🌐 URLs disponibles:
    echo    - Aplicación web: http://localhost:8000
    echo    - Documentación API: http://localhost:8000/api/docs
    echo    - ReDoc: http://localhost:8000/api/redoc
    echo.
    echo 🔑 Credenciales por defecto:
    echo    - Administrador: admin / admin123
    echo    - Profesor 1: profesor1 / profesor123
    echo    - Profesor 2: profesor2 / profesor123
    echo    - Profesor 3: profesor3 / profesor123
    echo.
    echo 📊 Para inicializar la base de datos con datos de muestra:
    echo    docker-compose exec web python -m app.utils.init_db
    echo.
    echo 📋 Para ver los logs:
    echo    docker-compose logs -f
    echo.
    echo 🛑 Para detener la aplicación:
    echo    docker-compose down
    echo.
    echo Presiona cualquier tecla para abrir la aplicación en el navegador...
    pause >nul
    start http://localhost:8000
) else (
    echo ❌ Error al iniciar la aplicación. Revisa los logs:
    docker-compose logs
    pause
    exit /b 1
)

