-- Tabla de Ligas
CREATE TABLE IF NOT EXISTS ligas (
    id_liga SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(100)
);

-- Tabla de Equipos
CREATE TABLE IF NOT EXISTS equipos (
    id_equipo INT PRIMARY KEY,
    nombre_oficial VARCHAR(150) NOT NULL,
    id_liga INT
);

-- Tabla de Partidos
CREATE TABLE IF NOT EXISTS partidos (
    id_partido INT PRIMARY KEY,
    id_liga INT,
    fecha_utc TIMESTAMP,
    id_local INT,
    id_visitante INT,
    estado VARCHAR(50)
);

-- Tabla de Historial de Cuotas
CREATE TABLE IF NOT EXISTS historial_cuotas (
    id_registro SERIAL PRIMARY KEY,
    id_partido INT,
    casa_apuestas VARCHAR(100),
    mercado VARCHAR(50),
    seleccion VARCHAR(100),
    cuota NUMERIC(5, 2),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Caché para Estadísticas (Evita bloqueos de API)
CREATE TABLE IF NOT EXISTS cache_estadisticas (
    nombre_equipo VARCHAR(150) PRIMARY KEY,
    xg NUMERIC(5, 2),
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Registro Histórico de Apuestas de Valor (Bitácora Contable)
CREATE TABLE IF NOT EXISTS registro_apuestas (
    id_registro SERIAL PRIMARY KEY,
    partido VARCHAR(150),
    casa_apuestas VARCHAR(100),
    seleccion VARCHAR(100),
    cuota_mercado NUMERIC(5, 2),
    ev_porcentaje NUMERIC(6, 2),
    stake_recomendado NUMERIC(6, 2),
    fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Calibración de Poder (Power Ratings Dinámicos)
CREATE TABLE IF NOT EXISTS power_ratings (
    nombre_equipo VARCHAR(150) PRIMARY KEY,
    xg_base NUMERIC(5, 2) NOT NULL,
    ultima_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);