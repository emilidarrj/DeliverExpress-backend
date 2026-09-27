from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Inicializamos la aplicación FastAPI
app = FastAPI(title="DeliverExpress API")

# Configuración de CORS (permite que el frontend se comunique con este backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de prueba para verificar que el servidor funcionass
@app.get("/")
def ruta_raiz():
    return {"mensaje": "¡El backend de DeliverExpress está funcionando perfectamente!"}