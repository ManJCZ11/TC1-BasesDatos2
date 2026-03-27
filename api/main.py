from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db
import requests
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

 # Esto asegura que las tablas se creen físicamente en PostgreSQL
models.Base.metadata.create_all(bind=engine)

# Se inicia la API
app = FastAPI(title="API de Reservas")                          

# Ruta de inicio
@app.get("/")                                                   
def inicio():
    return {"mensaje": "¡Bienvenido a la API de Reservas!"}

# Le dice a Swagger dónde se consigue el token para habilitar el candado
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# Middleware de seguridad: Se ejecuta antes de cada ruta para verificar el token y permisos
@app.middleware("http")
async def middleware_seguridad(request: Request, call_next):
    path = request.url.path
    method = request.method
    
    # Rutas que no ocupan llave para entrar
    rutas_publicas = ["/", "/docs", "/openapi.json", "/auth/login", "/auth/register"]
    get_publico = method == "GET" and (path.startswith("/restaurants") or path.startswith("/menus"))
    
    # Si la ruta es pública, pasa directo
    if path in rutas_publicas or get_publico:                                       
        return await call_next(request)         

    # Se revisa el token en el header de autorización
    auth_header = request.headers.get("Authorization")                              
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"detail": "No autorizado: Se necesita iniciar sesión"})
    
    # Se saca el token del header (el "Bearer ") para enviárselo a Keycloak
    token = auth_header.split(" ")[1] 

    try:
        IP_KEYCLOAK = "http://keycloak:8080"
        REALM_NAME = "BD2_TC1"
        # Se le pregunta a Keycloak por la información del usuario usando el token para validar si es correcto y no expiró
        url_userinfo = f"{IP_KEYCLOAK}/realms/{REALM_NAME}/protocol/openid-connect/userinfo"
        respuesta = requests.get(url_userinfo, headers={"Authorization": f"Bearer {token}"})

        if respuesta.status_code != 200:
            return JSONResponse(status_code=401, content={"detail": "Token inválido o expirado"})
        
        # Si el token es válido, se obtiene la información del usuario para verificar permisos
        datos_usuario = respuesta.json()
        roles = datos_usuario.get("realm_access", {}).get("roles", [])

        # Solo Clientes pueden reservar y ordenar, y ver sus datos
        rutas_cliente = path.startswith("/reservations") or path.startswith("/orders") 
                        or (method == "GET" and path == "/users/me")
        if rutas_cliente:
            if "Cliente" not in roles:
                return JSONResponse(status_code=403, content={"detail": "Acceso denegado: Se requiere rol de Cliente"})

        # Solo los Administradores pueden gestionar usuarios (GET, PUT, DELETE), gestionar menús (POST, PUT, DELETE) 
        # y agregar restaurantes
        rutas_admin = (
            (method == "POST" and (path.startswith("/restaurants") or path.startswith("/menus"))) or
            (method in ["PUT", "DELETE"] and (path.startswith("/users") or path.startswith("/menus")))
        )
        if rutas_admin and path == "/users/me":
            if "Administrador" not in roles:
                return JSONResponse(status_code=403, content={"detail": "Acceso denegado: Se requiere rol de Administrador"})

        request.state.user_data = datos_usuario                 # Guardarlos datos en el "state" para usarlos en las rutas

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Error de conexión: {str(e)}"})

    return await call_next(request)



# Rutas

#____________________________________________________________________________________________
# Auth

#POST /auth/register: Registra un nuevo usuario en keycloak y BD

@app.post("/auth/register", response_model=schemas.UsuarioRespuesta)
def registrar_usuario(usuario: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    IP_KEYCLOAK = "http://keycloak:8080"
    REALM_NAME = "BD2_TC1"
    ADMIN_USER = "UserTC1"          # Usuario para entrar a localhost:8080
    ADMIN_PASS = "KeycloakTC1"      # Contraseña para entrar a localhost:8080

    try:
        res_token = requests.post(f"{IP_KEYCLOAK}/realms/master/protocol/openid-connect/token", 
        data={
            "client_id": "admin-cli", 
            "username": ADMIN_USER, 
            "password": ADMIN_PASS, 
            "grant_type": "password"
        })
        token_admin = res_token.json()["access_token"]
        headers = {"Authorization": f"Bearer {token_admin}", "Content-Type": "application/json"}

        url_create_user = f"{IP_KEYCLOAK}/admin/realms/{REALM_NAME}/users"      # Crear el usuario en Keycloak
        nuevo_kc = {
            "username": usuario.nombre.replace(" ", "_").lower(),
            "email": usuario.email,
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": usuario.password,        # OJO: Les estamos poniendo clave '123' a todos por defecto
                "temporary": False
            }]
        }
        requests.post(url_create_user, json=nuevo_kc, headers=headers)

        respuesta_id = requests.get(f"{url_create_user}?email={usuario.email}", headers=headers)
        keycloak_id = respuesta_id.json()[0]["id"]                  # Obtener el ID de Keycloak

        nuevo_db = models.Usuario(                          # Guardarlo en PostgreSQL
            keycloakid=keycloak_id,
            nombre=usuario.nombre,
            email=usuario.email,
            rol=usuario.rol
        )
        db.add(nuevo_db)
        db.commit()
        db.refresh(nuevo_db)
        
        return nuevo_db

    except Exception as e:
        raise HTTPException(status_code=500, detail="Fallo en el sistema de registro")


#POST /auth/login: Inicio de sesión y obtención de JWT

@app.post("/auth/login")
def login_usuario(credenciales: OAuth2PasswordRequestForm = Depends()):
    IP_KEYCLOAK = "http://keycloak:8080"                                              # nombre contenedor Keycloak
    REALM_NAME = "BD2_TC1"                                                            # Nombre del Realm
    CLIENT_ID = "api_TC1BD"                                                           # Nombre del cliente en Keycloak
    url_token = f"{IP_KEYCLOAK}/realms/{REALM_NAME}/protocol/openid-connect/token"    #URL donde se obtiene el token
    payload = {                                                                       # Paquete de datos que Keycloak solicita
        "client_id": CLIENT_ID,
        "username": credenciales.username,
        "password": credenciales.password,
        "grant_type": "password",
        "scope": "openid"
    }
    try:                                                                              # Hacer llamada a Keycloak
        respuesta = requests.post(url_token, data=payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Servidor Keycloak no responde: {str(e)}")
        
    if respuesta.status_code == 200:                                                  # Evaluación de respuesta de Keycloak
        return respuesta.json()
    else:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")


#____________________________________________________________________________________________
# Usuario

#GET /users/me: Obtiene los detalles del usuario autenticado

@app.get("/users/me", response_model=schemas.UsuarioRespuesta)
def obtener_usuario(request: Request, db: Session = Depends(get_db)):
    keycloak_id = request.state.user_data["sub"]                   # Se saca el ID (código grande) de Keycloak (el sub)
                                                                   # que el middleware ya validó y guardó

    usuario = db.query(models.Usuario).filter(models.Usuario.keycloakid == keycloak_id).first()
    if not usuario:                                                                 # Valida que exista
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


#PUT /users/{id}: Actualiza un usuario existente

@app.put("/users/{id}", response_model=schemas.UsuarioRespuesta)
def actualizar_usuario(id: int, usuario_actualizado: schemas.UsuarioActualizar, db: Session = Depends(get_db)):
    usuario_db = db.query(models.Usuario).filter(models.Usuario.id == id).first()
    if not usuario_db:                                                     # Valida que exista
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario_db.nombre = usuario_actualizado.nombre
    usuario_db.email = usuario_actualizado.email
    usuario_db.rol = usuario_actualizado.rol

    db.commit()
    db.refresh(usuario_db)
    return usuario_db


# DELETE /users/{id}: Elimina un usuario existente

@app.delete("/users/{id}")
def eliminar_usuario(id: int, db: Session = Depends(get_db)):
    usuario_db = db.query(models.Usuario).filter(models.Usuario.id == id).first()
    if not usuario_db:                                                             # Valida que exista
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(usuario_db)
    db.commit()
    return {"mensaje": "Usuario eliminado exitosamente"}


#____________________________________________________________________________________________
# Restaurante

#POST /restaurants: Registra un nuevo restaurante

@app.post("/restaurants", response_model=schemas.RestauranteRespuesta)
def registrar_restaurante(restaurante: schemas.RestauranteCrear, db: Session = Depends(get_db)):  

    nuevo_restaurante = models.Restaurante(                     # Preparar los datos
        nombre=restaurante.nombre,
        direccion=restaurante.direccion,
        administradorid=restaurante.administradorid
    )
    db.add(nuevo_restaurante)                                   # Guardar en la base de datos
    db.commit()
    db.refresh(nuevo_restaurante)                               # Refrescar para obtener el ID
    return nuevo_restaurante                                    



#GET /restaurants: Obtiene la lista de restaurantes

@app.get("/restaurants", response_model=list[schemas.RestauranteRespuesta])
def obtener_restaurantes(db: Session = Depends(get_db)):        # Obtener todos los restaurantes de la base de datos
    restaurantes_db = db.query(models.Restaurante).all()           # Devolver la lista de restaurantes como respuesta
    return restaurantes_db