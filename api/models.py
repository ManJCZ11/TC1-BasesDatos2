from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DECIMAL, TIMESTAMP, Text
from database import Base

# 1. Molde de Usuario
class Usuario(Base):
    __tablename__ = "usuario"       # Así se llama la tabla real en tu base de datos
    id = Column(Integer, primary_key=True, index=True)
    keycloakid = Column(String, unique=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    rol = Column(String, nullable=False)

# 2. Restaurante
class Restaurante(Base):
    __tablename__ = "restaurante"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    direccion = Column(Text, nullable=False)
    administradorid = Column(Integer, ForeignKey("usuario.id"))

# 3. Mesa
class Mesa(Base):
    __tablename__ = "mesa"
    id = Column(Integer, primary_key=True, index=True)
    restauranteid = Column(Integer, ForeignKey("restaurante.id", ondelete="CASCADE"))
    numero_mesa = Column(Integer, nullable=False)
    capacidad_personas = Column(Integer, nullable=False)

# 4. Menú
class Menu(Base):
    __tablename__ = "menu"
    id = Column(Integer, primary_key=True, index=True)
    restauranteid = Column(Integer, ForeignKey("restaurante.id", ondelete="CASCADE"))
    nombre = Column(String, nullable=False)

# 5. Plato
class Plato(Base):
    __tablename__ = "plato"
    id = Column(Integer, primary_key=True, index=True)
    menuid = Column(Integer, ForeignKey("menu.id", ondelete="CASCADE"))
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    precio = Column(DECIMAL(10, 2), nullable=False)

# 6. Reserva
class Reserva(Base):
    __tablename__ = "reserva"
    id = Column(Integer, primary_key=True, index=True)
    clienteid = Column(Integer, ForeignKey("usuario.id"))
    mesaid = Column(Integer, ForeignKey("mesa.id"))
    fecha_hora = Column(TIMESTAMP, nullable=False)
    estado = Column(String, default="Pendiente")

# 7. Pedido
class Pedido(Base):
    __tablename__ = "pedido"
    id = Column(Integer, primary_key=True, index=True)
    clienteid = Column(Integer, ForeignKey("usuario.id"))
    restauranteid = Column(Integer, ForeignKey("restaurante.id"))
    fecha = Column(TIMESTAMP)
    recoger = Column(Boolean, default=False)
    estado = Column(String, default="En Preparación")

# 8. Detalle del Pedido
class DetallePedido(Base):
    __tablename__ = "detalle_pedido"
    id = Column(Integer, primary_key=True, index=True)
    pedidoid = Column(Integer, ForeignKey("pedido.id", ondelete="CASCADE"))
    platoid = Column(Integer, ForeignKey("plato.id"))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)