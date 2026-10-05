INSERT INTO Utilisateurs(id, mot_de_passe, name, email) VALUES
(1, 'azerty', 'jacques', 'jacques@ensai.fr'),
(2, 'admin' , 'admin'  , 'admin@ensai.fr'  ),
(4, 'a'     , 'jean'   , 'jean@ensai.fr'   );

INSERT INTO Historique(id, utilisateur_id) VALUES
(1, 1),
(2, 2),
(3, 4);

INSERT INTO Audit(id, historique_id, date_audit, statut, score, emissionCO2) VALUES
(1, 1, '01/01/1997', FALSE, NULL , NULL ),
(2, 1, '02/01/1997', TRUE , 98.9 , NULL ),
(3, 2, '12/10/2004', FALSE, 50.42, 800  ),
(4, 2, '12/10/2004', FALSE, 60.89, NULL ),
(5, 3, '24/06/2031', TRUE , 75   , 95.25),
(6, 3, '30/06/2031', FALSE, 74.01, 90.63),
(7, 3, '30/06/2031', TRUE , 77.23, 82.67);

INSERT INTO Fichier(id, audit_id, chemin, extension, score, complexite, emissionCO2) VALUES
(1 , 1, '', '.py'  , NULL , NULL       , NULL ),
(2 , 2, '', '.lock', 100  , NULL       , NULL ),
(3 , 2, '', '.py'  , 97.8 , NULL       , NULL ),
(4 , 3, '', '.py'  , 80.25, 'O(n^3)'   , 300  ),
(5 , 3, '', '.py'  , 40.25, 'O(n^2)'   , 200  ),
(6 , 3, '', '.py'  , 62.17, 'O(n^4)'   , 300  ),
(7 , 4, '', '.lock', 60.89, NULL       , NULL ),
(8 , 5, '', '.lock', 100  , NULL       , NULL ),
(9 , 5, '', '.py'  , 50   , 'O(n)'     , 95.25),
(10, 6, '', '.lock', 75   , NULL       , NULL ),
(11, 6, '', '.py'  , 73.02, 'O(n)'     , 90.63),
(12, 7, '', '.lock', 95   , NULL       , NULL ),
(13, 7, '', '.py'  , 59.46, 'O(log(n))', 82.67),