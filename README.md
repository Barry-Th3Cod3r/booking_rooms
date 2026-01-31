# 🏫 Booking Rooms - Sistema de Reservas de Aulas

Sistema web para la gestión de reservas de aulas en centros educativos. Permite a profesores y personal del centro reservar aulas de forma fácil y evitar conflictos de horarios.

![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-blue?logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?logo=postgresql)

## 📋 Características

- ✅ **Reserva de aulas** con detección automática de conflictos
- ✅ **Calendario visual** (vista día, semana, mes)
- ✅ **Gestión de usuarios** con roles (admin/usuario)
- ✅ **Panel de administración** para gestionar aulas, reservas y usuarios
- ✅ **"My Bookings"** - cada usuario puede ver y editar sus propias reservas
- ✅ **Temas personalizables** (claro, oscuro, personalizado)
- ✅ **Acceso remoto** via Cloudflare Tunnel (gratis)
- ✅ **Base de datos persistente** - los datos se guardan aunque reinicies

---

## 🚀 Instalación

### Requisitos

- **Docker Desktop** instalado ([descargar aquí](https://www.docker.com/products/docker-desktop/))
- **Git** (opcional, para clonar el repositorio)

### Paso 1: Descargar el proyecto

```bash
# Opción A: Clonar con Git
git clone https://github.com/Barry-Th3Cod3r/booking_rooms.git
cd booking_rooms

# Opción B: Descargar ZIP desde GitHub y descomprimir
```

### Paso 2: Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto (o copia `.env.example`):

```env
# Base de datos
POSTGRES_USER=booking
POSTGRES_PASSWORD=tu_contraseña_segura
POSTGRES_DB=booking_rooms

# Seguridad (genera una clave aleatoria)
SECRET_KEY=tu_clave_secreta_muy_larga_y_aleatoria

# Aplicación
DEBUG=false
```

### Paso 3: Iniciar la aplicación

```bash
docker-compose up -d
```

La primera vez tardará unos minutos en descargar las imágenes y construir los contenedores.

### Paso 4: Crear usuario administrador

```bash
# Genera un hash de contraseña
docker exec booking_backend python -c "
import bcrypt
password = 'tu_contraseña'
print(bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
"

# Inserta el usuario en la base de datos
docker exec booking_db psql -U booking -d booking_rooms -c "
INSERT INTO users (username, email, full_name, hashed_password, is_admin, is_active)
VALUES ('admin', 'tu@email.com', 'Nombre Admin', 'HASH_GENERADO', true, true);
"
```

### Paso 5: Acceder a la aplicación

| Servicio | URL |
|----------|-----|
| **Aplicación** | http://localhost |
| **API Docs** | http://localhost/api/docs |
| **Adminer (DB)** | http://localhost:8080 |

---

## 🌐 Acceso desde otros ordenadores (Red local del centro)

### Opción A: Acceso por IP local (solo red interna)

1. Encuentra la IP del ordenador host:
   - **Windows**: `ipconfig` → busca "IPv4 Address"
   - **macOS**: `ifconfig en0` → busca "inet"
   - **Linux**: `ip addr` → busca "inet"

2. Los demás ordenadores pueden acceder usando:
   ```
   http://192.168.x.x
   ```

### Opción B: Cloudflare Tunnel (acceso desde cualquier lugar)

Permite acceso desde móviles, tablets y ordenadores fuera de la red local.

1. Instala cloudflared:
   ```bash
   # macOS
   brew install cloudflared

   # Windows (PowerShell como Admin)
   winget install Cloudflare.cloudflared

   # Linux
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
   chmod +x cloudflared
   sudo mv cloudflared /usr/local/bin/
   ```

2. Inicia el túnel:
   ```bash
   cloudflared tunnel --url http://localhost:80
   ```

3. Copia la URL que aparece (ejemplo: `https://random-name.trycloudflare.com`)

4. Comparte esa URL con los usuarios

> ⚠️ La URL cambia cada vez que reinicias el túnel. Para una URL fija, considera usar un dominio propio con Cloudflare.

---

## 💻 Instalación por Sistema Operativo

### Windows

1. Instala [Docker Desktop para Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Reinicia el ordenador si te lo pide
3. Abre PowerShell y navega a la carpeta del proyecto:
   ```powershell
   cd C:\ruta\al\proyecto\booking_rooms
   docker-compose up -d
   ```

### macOS

1. Instala [Docker Desktop para Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Abre Terminal y ejecuta:
   ```bash
   cd /ruta/al/proyecto/booking_rooms
   docker-compose up -d
   ```

### Linux (Ubuntu/Debian)

1. Instala Docker:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   # Cierra sesión y vuelve a entrar
   ```

2. Instala Docker Compose:
   ```bash
   sudo apt install docker-compose-plugin
   ```

3. Inicia la aplicación:
   ```bash
   cd /ruta/al/proyecto/booking_rooms
   docker compose up -d
   ```

---

## 🔧 Comandos útiles

```bash
# Ver estado de los servicios
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar un servicio
docker-compose restart backend

# Parar todo
docker-compose down

# Parar y eliminar datos (⚠️ borra la base de datos)
docker-compose down -v

# Reconstruir después de cambios
docker-compose build --no-cache
docker-compose up -d
```

---

## 👥 Gestión de usuarios

### Desde la aplicación (recomendado)
1. Inicia sesión como administrador
2. Ve a ⚙️ **Settings** → **Users**
3. Añade nuevos usuarios con nombre, email y contraseña

### Desde Adminer (gestión directa de BD)
1. Accede a http://localhost:8080
2. Credenciales:
   - Sistema: PostgreSQL
   - Servidor: `db`
   - Usuario: (el de tu .env)
   - Contraseña: (la de tu .env)
   - Base de datos: `booking_rooms`

---

## 📁 Estructura del proyecto

```
booking_rooms/
├── app/                    # Backend FastAPI
│   ├── api/               # Endpoints de la API
│   ├── core/              # Configuración, seguridad, DB
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Schemas Pydantic
│   └── services/          # Lógica de negocio
├── frontend/              # Frontend React
│   ├── index.tsx          # Aplicación principal
│   └── index.css          # Estilos
├── nginx/                 # Configuración del proxy
├── docker-compose.yaml    # Orquestación de servicios
├── Dockerfile.backend     # Imagen del backend
└── .env                   # Variables de entorno (crear)
```

---

## 🔒 Seguridad

- Las contraseñas se almacenan hasheadas con bcrypt
- Autenticación via JWT tokens
- CORS configurado para el dominio
- Rate limiting en la API

---

## 📝 Licencia

MIT License - Uso libre para centros educativos.

---

## 🆘 Soporte

Si encuentras algún problema:
1. Revisa los logs: `docker-compose logs -f`
2. Reinicia los servicios: `docker-compose restart`
3. Abre un issue en GitHub

---

Desarrollado con ❤️ para facilitar la gestión de aulas en centros educativos.
