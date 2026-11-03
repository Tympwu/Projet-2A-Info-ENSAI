-----------------------------------------------------
-- Utilisateurs
-----------------------------------------------------
DROP TABLE IF EXISTS Utilisateurs CASCADE;

CREATE TABLE Utilisateurs (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mot_de_passe VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    email VARCHAR
);

-----------------------------------------------------
-- Audit
-----------------------------------------------------
CREATE TABLE Audit (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id INTEGER,
    date_audit DATE NOT NULL,
    statut VARCHAR DEFAULT NULL,
    score NUMERIC(4) DEFAULT NULL,
    emissionCO2 NUMERIC(4) DEFAULT NULL,
CONSTRAINT fk_Audit
FOREIGN KEY (utilisateur_id)
REFERENCES Utilisateurs(id) ON DELETE CASCADE
);


-----------------------------------------------------
-- Fichier
-----------------------------------------------------
CREATE TABLE Fichier (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    audit_id INTEGER,
    chemin VARCHAR UNIQUE NOT NULL,
    extension VARCHAR(20),
    score NUMERIC(4) DEFAULT NULL,
    complexite VARCHAR DEFAULT NULL,
    emissionCO2 NUMERIC(4) DEFAULT NULL,
CONSTRAINT fk_Fichier
FOREIGN KEY (audit_id)
REFERENCES Audit(id) ON DELETE CASCADE
);