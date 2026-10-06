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
-- Historique
-----------------------------------------------------
CREATE TABLE Historique(
	id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER,
CONSTRAINT fk_Historique 
FOREIGN KEY (utilisateur_id) 
REFERENCES Utilisateurs(id) ON DELETE CASCADE
);

-----------------------------------------------------
-- Audit
-----------------------------------------------------
CREATE TABLE Audit (
    id SERIAL PRIMARY KEY,
    historique_id INTEGER,
    date_audit DATE NOT NULL,
    statut BOOLEAN DEFAULT FALSE,
    score NUMERIC(4) DEFAULT NULL,
    emissionCO2 NUMERIC(4) DEFAULT NULL,
CONSTRAINT fk_Audit
FOREIGN KEY (historique_id)
REFERENCES Historique(id) ON DELETE CASCADE
);


-----------------------------------------------------
-- Fichier
-----------------------------------------------------
CREATE TABLE Fichier (
    id SERIAL PRIMARY KEY,
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