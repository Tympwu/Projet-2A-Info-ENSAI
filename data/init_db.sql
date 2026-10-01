-----------------------------------------------------
-- Utilisateurs
-----------------------------------------------------
DROP TABLE IF EXISTS Utilisateurs CASCADE;

CREATE TABLE Utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mot_de_passe VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    email VARCHAR
);

-----------------------------------------------------
-- Historique
-----------------------------------------------------
CREATE TABLE Historique(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER,
CONSTRAINT fk_Historique 
FOREIGN KEY (utilisateur_id) 
REFERENCES Utilisateurs(id) ON DELETE CASCADE
);

-----------------------------------------------------
-- Audit
-----------------------------------------------------
CREATE TABLE Audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    historique_id INTEGER,
    date_audit DATE NOT NULL,
    statut BOOLEAN DEFAULT FALSE,
    score NUMERIC(2) DEFAULT NULL,
    emissionCO2 NUMERIC(2) DEFAULT NULL,
CONSTRAINT fk_Audit
FOREIGN KEY (historique_id)
REFERENCES Historique(id) ON DELETE CASCADE
);


-----------------------------------------------------
-- Fichier
-----------------------------------------------------
CREATE TABLE Fichier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER,
    chemin VARCHAR UNIQUE NOT NULL,
    extension VARCHAR(20),
    score NUMERIC(2) DEFAULT NULL,
    complexite VARCHAR DEFAULT NULL,
    emissionCO2 NUMERIC(2) DEFAULT NULL,
CONSTRAINT fk_Fichier
FOREIGN KEY (audit_id)
REFERENCES Audit(id) ON DELETE CASCADE
);