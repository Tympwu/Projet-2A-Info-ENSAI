-- Données de démonstration.
-- Audit.score  : note sur 20 = (10 - pire CVSS des fichiers) + max(0, 10 - 1 point par 0,01 gCO2e)
-- Fichier.score : pire score CVSS (0 à 10) des dépendances du fichier
-- emissionCO2  : en gCO2e
INSERT INTO Utilisateurs(mot_de_passe, name, email) VALUES
('admin' , 'admin'  , 'admin@ensai.fr'  ),
('azerty', 'jacques', 'jacques@ensai.fr'),
('a'     , 'jean'   , 'jean@ensai.fr'   );

INSERT INTO Audit(utilisateur_id, date_audit, statut, score, complexite, emissionCO2) VALUES
(1, '01/01/1997', 'créé'  , NULL, NULL, NULL),
(1, '02/01/1997', 'échoué', NULL, NULL, NULL),
(2, '12/10/2004', 'refusé', 4.0 , 4   , 0.08),
(2, '12/10/2004', 'validé', 18.2, NULL, 0   ),
(3, '06/24/2031', 'refusé', 5.2 , 1   , 0.05),
(3, '06/30/2031', 'refusé', 9.5 , 1   , 0.03),
(3, '06/30/2031', 'validé', 18.0, 1   , 0.02);

INSERT INTO Fichier(audit_id, code, extension, score, complexite, emissionCO2) VALUES
(1, 'a', '.py'  , NULL, NULL, NULL ),
(2, 'b', '.lock', NULL, NULL, NULL ),
(2, 'c', '.py'  , NULL, NULL, NULL ),
(3, 'd', '.py'  , 8.0 , 3   , 0.03 ),
(3, 'e', '.py'  , 4.0 , 2   , 0.02 ),
(3, 'f', '.py'  , 6.2 , 4   , 0.03 ),
(4, 'g', '.lock', 1.8 , NULL, NULL ),
(5, 'h', '.lock', 9.8 , NULL, NULL ),
(5, 'i', '.py'  , 5.0 , 1   , 0.05 ),
(6, 'j', '.lock', 7.5 , NULL, NULL ),
(6, 'k', '.py'  , 7.3 , 1   , 0.03 ),
(7, 'l', '.lock', 0.0 , NULL, NULL ),
(7, 'm', '.py'  , 0.0 , 1   , 0.02 );
