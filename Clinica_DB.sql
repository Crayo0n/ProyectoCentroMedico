-- Crear base de datos
CREATE DATABASE Clinica_DB;
USE clinica_DB;

-- Tabla roles
CREATE TABLE roles (
    idrol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- Tabla medicos
CREATE TABLE medicos (
    idmedico INT AUTO_INCREMENT PRIMARY KEY,
    rfc VARCHAR(13) NOT NULL UNIQUE,
    nombrecompleto VARCHAR(255) NOT NULL,
    cedulaprofesional VARCHAR(20) NOT NULL UNIQUE,
    correo VARCHAR(255) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    idrol INT NOT NULL,
    FOREIGN KEY (idrol) REFERENCES roles(idrol)
);

-- Tabla pacientes
CREATE TABLE pacientes (
    idpaciente INT AUTO_INCREMENT PRIMARY KEY,
    idmedico INT NOT NULL,
    nombrecompleto VARCHAR(255) NOT NULL,
    fechanacimiento DATE NOT NULL,
    enfermedadescronicas TEXT,
    alergias TEXT,
    antecedentesfam TEXT,
    FOREIGN KEY (idmedico) REFERENCES medicos(idmedico)
);

-- Tabla citas
CREATE TABLE citas (
    idcita INT AUTO_INCREMENT PRIMARY KEY,
    idpaciente INT NOT NULL,
    fecha DATETIME NOT NULL,
    peso DECIMAL(5, 2),
    altura DECIMAL(5, 2),
    temperatura DECIMAL(4, 1),
    latidosmin INT,
    saturacionoxigeno DECIMAL(4, 1),
    glucosa DECIMAL(5, 2),
    FOREIGN KEY (idpaciente) REFERENCES pacientes(idpaciente)
);

-- Tabla diagnostico
CREATE TABLE diagnostico (
    iddiagnostico INT AUTO_INCREMENT PRIMARY KEY,
    idcita INT NOT NULL,
    sintomas TEXT,
    diagnostico TEXT,
    tratamiento TEXT,
    estudios TEXT,
    FOREIGN KEY (idcita) REFERENCES citas(idcita)
);


-- Inserts para roles (por si no los tienes)
INSERT INTO roles (idrol, nombre) VALUES
(3, 'Admin'),
(1, 'Médico');
 
 
 -- Inserts medicos (con idrol según tus roles)
INSERT INTO medicos (rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol) VALUES
('GMC1234567853', 'diego jota', '12345', 'house@example.com', 'housepass', 3), -- Admin
('JD12345601213', 'cristiano ronaldo', '23456', 'grey@example.com', 'greypass', 3),   -- Admin
('AW12378901213', 'messi', '34567', 'alexandra@example.com', 'alexpass', 1), -- Médico
('JS45678901212', 'neymar', '45678', 'johnsmith@example.com', 'johnpass', 1);  -- Médico

-- Inserts pacientes (idmedico de 1 a 4 según el orden anterior)
INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam) VALUES
(1, 'Albert Einstein', '1879-03-14', 'Hipertensión', 'Ninguna', 'Diabetes en familia'),
(2, 'Marie Curie', '1867-11-07', 'Asma', 'Penicilina', 'Cáncer en familia'),
(3, 'Isaac Newton', '1643-01-04', 'Ninguna', 'Ninguna', 'Hipertensión en familia'),
(4, 'Rosalind Franklin', '1920-07-25', 'Diabetes', 'Polvo', 'Asma en familia');

-- despues de la creacion de las tablas agregar status

ALTER TABLE pacientes
ADD COLUMN status INT DEFAULT 1; 

ALTER TABLE medicos
ADD COLUMN status INT DEFAULT 1;


select * from pacientes; 

select * from medicos; 