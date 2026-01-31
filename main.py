"""
FastAPI application for classroom booking system.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.api import auth_router, auth_google_router, users_router, classrooms_router, bookings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de reservas de aulas para institutos educativos",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include API routers
app.include_router(auth_router)
app.include_router(auth_google_router)
app.include_router(users_router)
app.include_router(classrooms_router)
app.include_router(bookings_router)


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "healthy", "version": settings.app_version}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    Root endpoint serving the main application.
    
    Returns:
        HTMLResponse: Main application page
    """
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema de Reservas IES</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .hero-section {
                padding: 100px 0;
                color: white;
                text-align: center;
            }
            .feature-card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 30px;
                margin: 20px 0;
                transition: transform 0.3s ease;
            }
            .feature-card:hover {
                transform: translateY(-5px);
            }
            .btn-custom {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                border: none;
                border-radius: 25px;
                padding: 12px 30px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .btn-custom:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="hero-section">
            <div class="container">
                <h1 class="display-4 mb-4">
                    <i class="fas fa-calendar-check"></i>
                    Sistema de Reservas IES
                </h1>
                <p class="lead mb-5">
                    Plataforma moderna para la gestión de reservas de aulas en institutos educativos
                </p>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="feature-card">
                            <i class="fas fa-users fa-3x mb-3"></i>
                            <h4>Gestión de Usuarios</h4>
                            <p>Control de acceso para profesores y administradores con autenticación segura</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="feature-card">
                            <i class="fas fa-door-open fa-3x mb-3"></i>
                            <h4>Reservas de Aulas</h4>
                            <p>Reserva fácilmente aulas disponibles con verificación de conflictos en tiempo real</p>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="feature-card">
                            <i class="fas fa-clock fa-3x mb-3"></i>
                            <h4>Calendario Visual</h4>
                            <p>Interfaz intuitiva para visualizar horarios y disponibilidad de aulas</p>
                        </div>
                    </div>
                </div>
                
                <div class="mt-5">
                    <a href="/api/docs" class="btn btn-custom btn-lg me-3">
                        <i class="fas fa-book"></i> Documentación API
                    </a>
                    <a href="/login" class="btn btn-outline-light btn-lg">
                        <i class="fas fa-sign-in-alt"></i> Iniciar Sesión
                    </a>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page():
    """
    Login page endpoint.
    
    Returns:
        HTMLResponse: Login page
    """
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Iniciar Sesión - Sistema de Reservas IES</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            .login-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                padding: 40px;
            }
            .btn-login {
                background: linear-gradient(45deg, #667eea, #764ba2);
                border: none;
                border-radius: 25px;
                padding: 12px 30px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .btn-login:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6 col-lg-4">
                    <div class="login-card">
                        <div class="text-center mb-4">
                            <i class="fas fa-calendar-check fa-3x text-primary mb-3"></i>
                            <h3 class="fw-bold">Iniciar Sesión</h3>
                            <p class="text-muted">Sistema de Reservas IES</p>
                        </div>
                        
                        <form id="loginForm">
                            <div class="mb-3">
                                <label for="username" class="form-label">
                                    <i class="fas fa-user"></i> Usuario
                                </label>
                                <input type="text" class="form-control" id="username" name="username" required>
                            </div>
                            
                            <div class="mb-4">
                                <label for="password" class="form-label">
                                    <i class="fas fa-lock"></i> Contraseña
                                </label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary btn-login">
                                    <i class="fas fa-sign-in-alt"></i> Entrar
                                </button>
                            </div>
                        </form>
                        
                        <div class="text-center mt-4">
                            <a href="/api/docs" class="text-decoration-none">
                                <i class="fas fa-book"></i> Ver Documentación API
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            document.getElementById('loginForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                try {
                    const response = await fetch('/auth/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ username, password })
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        localStorage.setItem('access_token', data.access_token);
                        alert('¡Inicio de sesión exitoso!');
                        // Redirect to dashboard or API docs
                        window.location.href = '/api/docs';
                    } else {
                        const error = await response.json();
                        alert('Error: ' + error.detail);
                    }
                } catch (error) {
                    alert('Error de conexión: ' + error.message);
                }
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
