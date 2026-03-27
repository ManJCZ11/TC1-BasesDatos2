from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import models, schemas
from database import engine, get_db
import requests
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv

load_dotenv()

 # Esto asegura que las tablas se creen físicamente en PostgreSQL
models.Base.metadata.create_all(bind=engine)

# Se inicia la API
app = FastAPI(title="API de Reservas")                          
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # permite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    # Rutas públicas
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
        # Se le pregunta a Keycloak por la información del usuario usando el token para validar si es correcto y no expiró
        url_userinfo = f"{os.getenv('IP_KEYCLOAK')}/realms/{os.getenv('REALM_NAME')}/protocol/openid-connect/userinfo"
        respuesta = requests.get(url_userinfo, headers={"Authorization": f"Bearer {token}"})

        if respuesta.status_code != 200:
            return JSONResponse(status_code=401, content={"detail": "Token inválido o expirado"})
        
        # Si el token es válido, se obtiene la información del usuario para verificar permisos
        datos_usuario = respuesta.json()
        roles = datos_usuario.get("realm_access", {}).get("roles", [])
        print ("rol: ", roles)

        # Si alguien quiere ver su propio perfil, se deja pasar
        if path == "/users/me" and method == "GET":
            request.state.user_data = datos_usuario
            return await call_next(request)

        # Solo Clientes pueden reservar y ordenar
        rutas_cliente = path.startswith("/reservations") or path.startswith("/orders") 
        if rutas_cliente:
            if "Cliente" not in roles:
                return JSONResponse(status_code=403, content={"detail": "Acceso denegado: Se requiere rol de Cliente"})

        # Solo los Administradores pueden gestionar usuarios (GET, PUT, DELETE), gestionar menús (POST, PUT, DELETE) 
        # y agregar restaurantes
        rutas_admin = (
            (method == "POST" and (path.startswith("/restaurants") or path.startswith("/menus"))) or
            (method in ["PUT", "DELETE"] and (path.startswith("/users") or path.startswith("/menus"))) or
            (method == "GET" and path.startswith("/users"))
        )

        if rutas_admin:
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

    # Validación de que el correo no esté registrado en la base de datos
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado en el sistema")
    try:
        # Se ingresa a Keycloak poniendo el username y password
        respuesta_token = requests.post(f"{os.getenv('IP_KEYCLOAK')}/realms/master/protocol/openid-connect/token", 
        data={
            "client_id": "admin-cli", # Cliente predefinido en Keycloak que tiene permisos de administración
            "username": os.getenv('KEYCLOAK_ADMIN'), 
            "password": os.getenv('KEYCLOAK_ADMIN_PASSWORD'), 
            "grant_type": "password"
        })

        if respuesta_token.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudo obtener acceso administrativo de Keycloak")

        # Si la autenticación es exitosa, se obtiene el token de acceso para usarlo en las siguientes solicitudes a Keycloak
        token_admin = respuesta_token.json()["access_token"] # 
        # Se prepara el header con el token para autorizar las solicitudes de administración a Keycloak
        headers_admin = {"Authorization": f"Bearer {token_admin}", "Content-Type": "application/json"}

        # Se crea el usuario en Keycloak
        url_crear_user = f"{os.getenv('IP_KEYCLOAK')}/admin/realms/{os.getenv('REALM_NAME')}/users"
        nuevo_kc = {
            "username": usuario.email,
            "firstName": usuario.nombre,
            "lastName": usuario.apellido,
            "email": usuario.email,
            "enabled": True,
            "emailVerified": True,
            "credentials": [{
                "type": "password",
                "value": usuario.password,     
                "temporary": False
            }]
        }
        respuesta_crear_user = requests.post(url_crear_user, json=nuevo_kc, headers=headers_admin)

        # Validar que el usuario no exista ya en Keycloak
        if respuesta_crear_user.status_code == 409:
            raise HTTPException(status_code=400, detail="El usuario ya existe en Keycloak")

        # Validar que la creación del usuario en Keycloak fue exitosa
        if respuesta_crear_user.status_code != 201:
            raise HTTPException(status_code=400, detail=f"Error al crear usuario: {respuesta_crear_user.text}")

        # Obtener el ID del usuario recién creado en Keycloak para guardarlo en PostgreSQL
        respuesta_id = requests.get(f"{url_crear_user}?email={usuario.email}", headers=headers_admin)
        datos_usuario_kc = respuesta_id.json()   

        # Validar que se haya podido recuperar el ID de Keycloak
        if not datos_usuario_kc:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el ID de Keycloak tras la creación")
            
        keycloak_id = datos_usuario_kc[0]["id"]       

        # Obtener el ID del rol que se quiere asignar al usuario recién creado
        url_obtener_rol = f"{os.getenv('IP_KEYCLOAK')}/admin/realms/{os.getenv('REALM_NAME')}/roles/{usuario.rol}"
        respuesta_rol = requests.get(url_obtener_rol, headers=headers_admin)

        if respuesta_rol.status_code == 200:
            datos_rol = respuesta_rol.json()
            
            # Asignar el rol al usuario usando el ID del usuario y el ID del rol
            url_asignar_rol = f"{os.getenv('IP_KEYCLOAK')}/admin/realms/{os.getenv('REALM_NAME')}/users/{keycloak_id}/role-mappings/realm"
            
            # Keycloak exige que se le envíe como una lista de diccionarios
            payload_rol = [{
                "id": datos_rol["id"],
                "name": datos_rol["name"]
            }]
            
            respuesta_asignar = requests.post(url_asignar_rol, json=payload_rol, headers=headers_admin)
            
            if respuesta_asignar.status_code not in [200, 204]:
                raise HTTPException(status_code=500, detail="Usuario creado, pero falló la asignación del rol en Keycloak")
        else:
            raise HTTPException(status_code=400, detail=f"El rol '{usuario.rol}' no existe en Keycloak.")

        nombre_completo = f"{usuario.nombre} {usuario.apellido}"

        # Guardar el usuario en la base de datos PostgreSQL con el ID de Keycloak
        nuevo_db = models.Usuario(          
            keycloakid=keycloak_id,
            nombre=nombre_completo,
            email=usuario.email,
            rol=usuario.rol
        )
        db.add(nuevo_db)
        db.commit()
        db.refresh(nuevo_db)
        
        return nuevo_db

    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



#POST /auth/login: Inicio de sesión y obtención de JWT

@app.post("/auth/login")
def login_usuario(credenciales: OAuth2PasswordRequestForm = Depends()):
    # URL donde se obtiene el token
    url_token = f"{os.getenv('IP_KEYCLOAK')}/realms/{os.getenv('REALM_NAME')}/protocol/openid-connect/token"
    
    # Paquete de datos que Keycloak solicita 
    payload = {                                                                                                                              
        "client_id": os.getenv('CLIENT_ID'),
        "client_secret": os.getenv('CLIENT_SECRET'),
        "username": credenciales.username,
        "password": credenciales.password,
        "grant_type": "password",
        "scope": "openid"
    }
    try:                      
        # Se le pregunta a Keycloak por el token usando las credenciales que el usuario ingresó                                                        
        respuesta = requests.post(url_token, data=payload)

        # Evaluación de respuesta de Keycloak
        if respuesta.status_code == 200:                                                  
            return respuesta.json()
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="No se pudo conectar con el servidor de identidad (Keycloak)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")



#____________________________________________________________________________________________
# Usuario

#GET /users/me: Obtiene los detalles del usuario autenticado

@app.get("/users/me", response_model=schemas.UsuarioRespuesta, dependencies=[Depends(oauth2_scheme)])
def obtener_usuario_logueado(request: Request, db: Session = Depends(get_db)):
    
    try:
        # Se saca el ID de Keycloak que el middleware guardó
        keycloak_id = request.state.user_data["sub"]                                                                          
        
        # Se busca el usuario en la base de datos
        usuario = db.query(models.Usuario).filter(models.Usuario.keycloakid == keycloak_id).first()

        # Validación de que el usuario exista
        if not usuario:                                                                 
            raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")
        return usuario
        
    except HTTPException:
        # Errores manejados explícitamente
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al buscar el usuario: {str(e)}")



#GET /users/{id}: Obtiene los detalles de un usuario existente (solo para Admin)

@app.get("/users/{id}", response_model=schemas.UsuarioRespuesta, dependencies=[Depends(oauth2_scheme)])
def obtener_usuario(id: int, request: Request, db: Session = Depends(get_db)):
    
    try:
        # Se busca el usuario en la base de datos usando el ID
        usuario = db.query(models.Usuario).filter(models.Usuario.id == id).first()

        if not usuario:                                                     
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario
        
    except HTTPException:
        # Errores manejados explícitamente
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al buscar el usuario: {str(e)}")



#PUT /users/{id}: Actualiza un usuario existente

@app.put("/users/{id}", response_model=schemas.UsuarioRespuesta, dependencies=[Depends(oauth2_scheme)])
def actualizar_usuario(id: int, datos_nuevos: schemas.UsuarioActualizar, request: Request, db: Session = Depends(get_db)):
    try:
    
        # Buscar el usuario en la base de datos 
        usuario_db = db.query(models.Usuario).filter(models.Usuario.id == id).first()
        if not usuario_db:                                                     # Valida que exista
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Se ingresa a Keycloak poniendo el username y password
        respuesta_token = requests.post(f"{os.getenv('IP_KEYCLOAK')}/realms/master/protocol/openid-connect/token", 
        data={
            "client_id": "admin-cli", # Cliente predefinido en Keycloak que tiene permisos de administración
            "username": os.getenv('KEYCLOAK_ADMIN'), 
            "password": os.getenv('KEYCLOAK_ADMIN_PASSWORD'), 
            "grant_type": "password"
        })

        if respuesta_token.status_code != 200:
            raise HTTPException(status_code=500, detail="No se pudo obtener acceso administrativo de Keycloak")

        # Si la autenticación es exitosa, se obtiene el token de acceso para usarlo en las siguientes solicitudes a Keycloak
        token_admin = respuesta_token.json()["access_token"] # 
        # Se prepara el header con el token para autorizar las solicitudes de administración a Keycloak
        headers_admin = {"Authorization": f"Bearer {token_admin}", "Content-Type": "application/json"}
        
        url_kc_usuario = f"{os.getenv('IP_KEYCLOAK')}/admin/realms/{os.getenv('REALM_NAME')}/users/{usuario_db.keycloakid}"
        update_kc = {
            "firstName": datos_nuevos.nombre,
            "lastName": datos_nuevos.apellido
        }
        requests.put(url_kc_usuario, json=update_kc, headers=headers_admin)

        nombre_completo = f"{datos_nuevos.nombre} {datos_nuevos.apellido}"

        # Actualizar en la base de datos
        usuario_db.nombre = nombre_completo

        db.commit()
        db.refresh(usuario_db)
        return usuario_db

    except HTTPException:
        # Errores manejados explícitamente
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")



# DELETE /users/{id}: Elimina un usuario existente

@app.delete("/users/{id}", dependencies=[Depends(oauth2_scheme)])
def eliminar_usuario(id: int, request: Request, db: Session = Depends(get_db)):
    
    # Buscar el usuario en la Base de Datos
    usuario_db = db.query(models.Usuario).filter(models.Usuario.id == id).first()
    
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        #   Obtiene el token de administrador para hacer las solicitudes a Keycloak
        respuesta_token = requests.post(f"{os.getenv('IP_KEYCLOAK')}/realms/master/protocol/openid-connect/token", 
        data={
            "client_id": "admin-cli",
            "username": os.getenv('KEYCLOAK_ADMIN'), 
            "password": os.getenv('KEYCLOAK_ADMIN_PASSWORD'), 
            "grant_type": "password"
        })

        if respuesta_token.status_code != 200:
            raise HTTPException(status_code=500, detail="Error de autenticación administrativa en Keycloak")

        token_admin = respuesta_token.json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        # Eliminar el usuario en Keycloak usando su ID
        url_eliminar_kc = f"{os.getenv('IP_KEYCLOAK')}/admin/realms/{os.getenv('REALM_NAME')}/users/{usuario_db.keycloakid}"
        respuesta_kc = requests.delete(url_eliminar_kc, headers=headers_admin)

        if respuesta_kc.status_code not in [204, 404]:
            raise HTTPException(status_code=500, detail="No se pudo eliminar el usuario en Keycloak")

        # Elimina el usuario en la base de datos
        db.delete(usuario_db)
        db.commit()

        return {"mensaje": "Usuario eliminado exitosamente de ambos sistemas"}

    except HTTPException:
        # Errores manejados explícitamente
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar: {str(e)}")



#____________________________________________________________________________________________
# Restaurante

# POST /restaurants: Registrar un nuevo restaurante (Solo Admin)

@app.post("/restaurants", response_model=schemas.RestauranteRespuesta, dependencies=[Depends(oauth2_scheme)])
def registrar_restaurante(restaurante: schemas.RestauranteCrear, request: Request, db: Session = Depends(get_db)):
    try:
        # Se saca el ID de Keycloak que el middleware guardó
        keycloak_id = request.state.user_data["sub"]                                                                          
        
        # Se busca el usuario en la base de datos
        admin = db.query(models.Usuario).filter(models.Usuario.keycloakid == keycloak_id).first()

        if not admin:
            raise HTTPException(status_code=404, detail="El usuario autenticado no existe en la base de datos local")

        # # Crear el restaurante en la base de datos con el ID del administrador que lo creó
        nuevo_restaurante = models.Restaurante(
            nombre=restaurante.nombre,
            direccion=restaurante.direccion,
            administradorid=admin.id
        )

        # 4. GUARDAR EN LA BASE DE DATOS
        db.add(nuevo_restaurante)
        db.commit()
        db.refresh(nuevo_restaurante)

        return nuevo_restaurante

    except HTTPException:
        # Errores manejados explícitamente
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear el restaurante: {str(e)}")                               



#GET /restaurants: Obtiene la lista de restaurantes

@app.get("/restaurants", response_model=list[schemas.RestauranteRespuesta])
def obtener_restaurantes(db: Session = Depends(get_db)):               # Obtener todos los restaurantes de la base de datos
    restaurantes_db = db.query(models.Restaurante).all()               # Devolver la lista de restaurantes como respuesta
    return restaurantes_db

