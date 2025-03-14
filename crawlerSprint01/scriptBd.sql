DROP DATABASE IF EXISTS infrawatch;
CREATE DATABASE infrawatch;
USE infrawatch;

CREATE TABLE Empresa (
	idEmpresa INT PRIMARY KEY auto_increment,
    nome VARCHAR(60) NOT NULL,
    cnpj CHAR(14) UNIQUE NOT NULL
);

CREATE TABLE Usuario (
	idUsuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(60) NOT NULL,
    email VARCHAR(80) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    fkEmpresa INT NOT NULL,
    CONSTRAINT fk_Empresa foreign key (fkEmpresa) REFERENCES Empresa(idEmpresa)
);

CREATE TABLE Servidor (
	uuidPlacaMae VARCHAR(255) PRIMARY KEY,
    tagName VARCHAR(80) NOT NULL,
    cpuCores INT NOT NULL,
    cpuThreads INT NOT NULL,
    RAM	INT NOT NULL,
    SO VARCHAR(40) NOT NULL,
    version VARCHAR(20) NOT NULL,
    fkEmpresa INT NOT NULL,
    CONSTRAINT fk_Empresa_Servidor foreign key (fkEmpresa) REFERENCES Empresa(idEmpresa)
);

CREATE TABLE GPU (
	uuid VARCHAR(255) PRIMARY KEY,
    nome VARCHAR(80) NOT NULL,
    VRAM INT NOT NULL,
    fkServidor VARCHAR(255) NOT NULL,
    CONSTRAINT fk_Servidor foreign key (fkServidor) REFERENCES Servidor(uuidPlacaMae)
);

CREATE TABLE RegistroGPU (
	idRegistro INT PRIMARY KEY AUTO_INCREMENT,
    usoGPU DOUBLE NOT NULL,
	usoVRAM INT NOT NULL,
    temperatura INT NOT NULL,
    dtRegistro timestamp DEFAULT current_timestamp NOT NULL,
    fkGPU VARCHAR(255) NOT NULL,
    CONSTRAINT fk_gpu foreign key (fkGPU) REFERENCES GPU(uuid)
);


CREATE TABLE RegistroServidor (
	idRegistro INT PRIMARY KEY AUTO_INCREMENT,
    usoCPU INT NOT NULL,
    usoRAM INT NOT NULL,
    clock DOUBLE NOT NULL,
    dtRegistro timestamp DEFAULT current_timestamp NOT NULL,
    fkServidor VARCHAR(255) NOT NULL,
    CONSTRAINT fk_Servidor_Servidor_monitoring FOREIGN KEY (fkServidor) REFERENCES Servidor(uuidPlacaMae)
);


INSERT INTO Empresa (nome, cnpj) VALUES 
('Irender', '12345678901234');

INSERT INTO Usuario (nome, email, senha, fkEmpresa) VALUES
("Bryan Rocha", "bryan.grocha@sptech.school", "12345678", 1);



