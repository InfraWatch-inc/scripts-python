-- Active: 1741828804228@@54.198.115.160@3306
DROP DATABASE IF EXISTS infrawatch;
CREATE DATABASE infrawatch;
USE infrawatch;

CREATE TABLE Company (
	idCompany INT PRIMARY KEY auto_increment,
    name VARCHAR(60) NOT NULL,
    cnpj CHAR(14) UNIQUE NOT NULL
);

CREATE TABLE User (
	idUser INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(60) NOT NULL,
    email VARCHAR(80) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    fkCompany INT NOT NULL,
    CONSTRAINT fk_company foreign key (fkCompany) REFERENCES Company(idCompany)
);

CREATE TABLE Server (
	uuidMotherboard VARCHAR(255) PRIMARY KEY,
    cpuCores INT NOT NULL,
    cpuThreads INT NOT NULL,
    RAM	INT NOT NULL,
    SO VARCHAR(40) NOT NULL,
    version VARCHAR(45) NOT NULL,
    fkCompany INT NOT NULL,
    CONSTRAINT fk_company_server foreign key (fkCompany) REFERENCES Company(idCompany)
);

CREATE TABLE GPU (
	uuid VARCHAR(255) PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    VRAM INT NOT NULL,
    fkServer VARCHAR(255) NOT NULL,
    CONSTRAINT fk_server foreign key (fkServer) REFERENCES Server(uuidMotherboard)
);

CREATE TABLE GPUMonitoring (
	idRegister INT PRIMARY KEY AUTO_INCREMENT,
    GPUload DOUBLE NOT NULL,
	vramUsed INT NOT NULL,
    temperature INT NOT NULL,
    dtRegister timestamp DEFAULT current_timestamp NOT NULL,
    fkGPU VARCHAR(255) NOT NULL,
    CONSTRAINT fk_gpu foreign key (fkGPU) REFERENCES GPU(uuid)
);


CREATE TABLE ServerMonitoring (
	idRegister INT PRIMARY KEY AUTO_INCREMENT,
    cpuLoad INT NOT NULL,
    ramUsed INT NOT NULL,
    clock DOUBLE NOT NULL,
    dtRegister timestamp DEFAULT current_timestamp NOT NULL,
    fkServer VARCHAR(255) NOT NULL,
    CONSTRAINT fk_server_server_monitoring FOREIGN KEY (fkServer) REFERENCES Server(uuidMotherboard)
);


INSERT INTO Company (name, cnpj) VALUES 
('Irender', '12345678901234');

INSERT INTO User (name, email, password, fkCompany) VALUES
("Bryan Rocha", "bryan.grocha@sptech.school", "12345678", 1);



