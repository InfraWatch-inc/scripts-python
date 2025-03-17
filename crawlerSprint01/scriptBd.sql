DROP DATABASE IF EXISTS infrawatch;
CREATE DATABASE infrawatch;
USE infrawatch;

CREATE TABLE Endereco (
    idEndereco INT PRIMARY KEY AUTO_INCREMENT,
    cep CHAR(15) NOT NULL,
    logradouro VARCHAR(45) NOT NULL,
    numero INT NOT NULL,
    cidade VARCHAR(80) NOT NULL,
    estado CHAR(2) NOT NULL
);

CREATE TABLE Empresa (
	idEmpresa INT PRIMARY KEY auto_increment,
    razaoSocial VARCHAR(60) NOT NULL,
    tinNumber CHAR(14) UNIQUE NOT NULL,
    fkEndereco INT NOT NULL,
    CONSTRAINT fk_Endereco foreign key (fkEndereco) REFERENCES Endereco(idEndereco)
);


CREATE TABLE Usuario (
	idUsuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(60) NOT NULL,
    email VARCHAR(80) UNIQUE NOT NULL,
    nif CHAR(16) NOT NULL,
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
    version VARCHAR(45) NOT NULL,
    fkEmpresa INT NOT NULL,
    CONSTRAINT fk_company_server foreign key (fkEmpresa) REFERENCES Empresa(idEmpresa)
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

INSERT INTO Endereco (cep, logradouro, numero, cidade, estado) VALUES 
('12345-678', 'Main St', '100', 'New York', 'NY');

INSERT INTO Empresa (razaoSocial, tinNumber, fkEndereco) VALUES 
('Irender', '12345678901234', 1);

INSERT INTO Usuario (nome, email, nif, senha, fkEmpresa) VALUES
("Bryan Rocha", "bryan.grocha@sptech.school", "1234567890123456", "12345678", 1);



