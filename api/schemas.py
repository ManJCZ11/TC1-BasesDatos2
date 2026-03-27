from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from decimal import Decimal


#Usuario

class UsuarioLogin(BaseModel):          # Keycloak
    username: str  
    password: str


class UsuarioCrear(BaseModel):          # Lo que se pide cuando alguien se registra
    nombre: str
    apellido: str
    email: EmailStr
    rol: str
    password: str


class UsuarioActualizar(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None


class UsuarioRespuesta(BaseModel):      # Lo que la API responde (incluye el ID que generó la base de datos)
    id: int
    keycloakid: str
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None

    class Config:
        from_attributes = True  # Le dice a Pydantic que traduzca desde la base de datos


#Restaurante

class RestauranteCrear(BaseModel):
    nombre: str
    direccion: str


class RestauranteActualizar(BaseModel):                                 # No sale en la tabla
    nombre: Optional[str] = None
    direccion: Optional[str] = None


class RestauranteRespuesta(BaseModel):
    id: int
    nombre: str
    direccion: str
    administradorid: int

    class Config:
        from_attributes = True


#Mesa

class MesaCrear(BaseModel):                                             # No sale en la tabla
    restauranteid: int
    numero_mesa: int
    capacidad_personas: int


class MesaRespuesta(BaseModel):                                         # No sale en la tabla
    id: int
    restauranteid: int
    numero_mesa: int
    capacidad_personas: int

    class Config:
        from_attributes = True


#Menú

class MenuCrear(BaseModel):
    restauranteid: int
    nombre: str


class MenuActualizar(BaseModel):
    nombre: Optional[str] = None


class MenuRespuesta(BaseModel):
    id: int
    restauranteid: int
    nombre: str

    class Config:
        from_attributes = True


#Plato

class PlatoCrear(BaseModel):                                               # No sale en la tabla
    menuid: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal


class PlatoRespuesta(BaseModel):                                        # No sale en la tabla
    id: int
    menuid: int
    nombre: str
    descripcion: Optional[str]
    precio: Decimal

    class Config:
        from_attributes = True


#Reserva
class ReservaCrear(BaseModel):
    clienteid: int
    mesaid: int
    fecha_hora: datetime
    # No se pide el estado porque por defecto siempre entra como Pendiente


class ReservaActualizarEstado(BaseModel):                               # No sale en la tabla
    estado: str # Para cambiar de "Pendiente" a "Confirmada" o "Cancelada"


class ReservaRespuesta(BaseModel):
    id: int
    clienteid: int
    mesaid: int
    fecha_hora: datetime
    estado: str

    class Config:
        from_attributes = True


#Pedido y detalle
class PedidoCrear(BaseModel):
    clienteid: int
    restauranteid: int
    recoger: bool = False


class PedidoRespuesta(BaseModel):
    id: int
    clienteid: int
    restauranteid: int
    fecha: datetime
    recoger: bool
    estado: str

    class Config:
        from_attributes = True