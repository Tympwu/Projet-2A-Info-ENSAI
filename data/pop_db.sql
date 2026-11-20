INSERT INTO Utilisateurs(mot_de_passe, name, email) VALUES
('admin' , 'admin'  , 'admin@ensai.fr'  ),
('azerty', 'jacques', 'jacques@ensai.fr'),
('a'     , 'jean'   , 'jean@ensai.fr'   );

INSERT INTO Audit(utilisateur_id, date_audit, statut, score, complexite, emissionCO2) VALUES
(1, '01/01/1997', 'créé'  , NULL, NULL, NULL ),
(1, '02/01/1997', 'échoué', 4   , NULL, NULL ),
(2, '12/10/2004', 'refusé', 6   , 4   , 800  ),
(2, '12/10/2004', 'validé', 3   , NULL, NULL ),
(3, '06/24/2031', 'refusé', 9   , 1   , 95.25),
(3, '06/30/2031', 'refusé', 7   , 1   , 90.63),
(3, '06/30/2031', 'validé', 2   , 1   , 82.67);

INSERT INTO Fichier(audit_id, code, extension, score, complexite, emissionCO2) VALUES
(1, 'a', '.py'  , NULL , NULL, NULL ),
(2, 'b', '.lock', 100  , NULL, NULL ),
(2, 'c', '.py'  , 97.8 , NULL, NULL ),
(3, 'd', '.py'  , 80.25, 3   , 300  ),
(3, 'e', '.py'  , 40.25, 2   , 200  ),
(3, 'f', '.py'  , 62.17, 4   , 300  ),
(4, 'g', '.lock', 60.89, NULL, NULL ),
(5, 'h', '.lock', 100  , NULL, NULL ),
(5, 'i', '.py'  , 50   , 1   , 95.25),
(6, 'j', '.lock', 75   , NULL, NULL ),
(6, 'k', '.py'  , 73.02, 1   , 90.63),
(7, 'l', '.lock', 95   , NULL, NULL ),
(7, 'm', '.py'  , 59.46, 1   , 82.67);