from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db

# Esto asegura que las tablas se creen físicamente en PostgreSQL
models.Base.metadata.create_all(bind=engine)

# Se inicia la API
app = FastAPI(title="API de Reservas")

# Ruta de inicio
@app.get("/")
def inicio():
    return {"mensaje": "¡Bienvenido a la API de Reservas!"}


# Rutas

# Usuario

@app.post("/users/register", response_model=schemas.UsuarioRespuesta)
def registrar_usuario(usuario: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    nuevo_usuario = models.Usuario(
        keycloakid=usuario.keycloakid,
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario


# Restaurante

@app.post("/restaurants", response_model=schemas.RestauranteRespuesta)
def crear_restaurante(restaurante: schemas.RestauranteCrear, db: Session = Depends(get_db)):
    
    # A. Preparar los datos
    nuevo_restaurante = models.Restaurante(
        nombre=restaurante.nombre,
        direccion=restaurante.direccion,
        administradorid=restaurante.administradorid
    )
    
    # B. Guardar en la base de datos
    db.add(nuevo_restaurante)
    db.commit()
    
    # C. Refrescar para obtener el ID
    db.refresh(nuevo_restaurante)
    
    # D. Devolver la respuesta
    return nuevo_restaurante