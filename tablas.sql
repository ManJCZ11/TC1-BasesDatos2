--Usuario
CREATE TABLE Usuario (
    id SERIAL PRIMARY KEY,
    keycloakID VARCHAR(255) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    rol VARCHAR(50) NOT NULL -- cliente o administrador
);

--Restaurante
CREATE TABLE Restaurante (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion TEXT NOT NULL,
    administradorID INT REFERENCES Usuario(id)
);

--Mesa
CREATE TABLE Mesa (
    id SERIAL PRIMARY KEY,
    restauranteID INT REFERENCES Restaurante(id) ON DELETE CASCADE,
    numero_mesa INT NOT NULL,
    capacidad_personas INT NOT NULL
);

--Menú
CREATE TABLE Menu (
    id SERIAL PRIMARY KEY,
    restauranteID INT REFERENCES Restaurante(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL
);

--Plato
CREATE TABLE Plato (
    id SERIAL PRIMARY KEY,
    menuID INT REFERENCES Menu(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL
);

--Reserva
CREATE TABLE Reserva (
    id SERIAL PRIMARY KEY,
    clienteID INT REFERENCES Usuario(id),
    mesaID INT REFERENCES Mesa(id),
    fecha_hora TIMESTAMP NOT NULL,
    estado VARCHAR(50) DEFAULT 'Pendiente' -- Pendiente, Confirmada, Cancelada
);

--Pedido
CREATE TABLE Pedido (
    id SERIAL PRIMARY KEY,
    clienteID INT REFERENCES Usuario(id),
    restauranteID INT REFERENCES Restaurante(id),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recoger BOOLEAN DEFAULT FALSE,
    estado VARCHAR(50) DEFAULT 'En Preparación'
);

--Detalle_Pedido
CREATE TABLE Detalle_Pedido (
    id SERIAL PRIMARY KEY,
    pedidoID INT REFERENCES Pedido(id) ON DELETE CASCADE,
    platoID INT REFERENCES Plato(id),
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL
);