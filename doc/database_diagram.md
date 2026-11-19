# Diagramme de la base de donnée

Ce diagramme est codé avec [mermaid](https://mermaid.js.org/syntax/classDiagram.html) :

* avantage : facile à coder
* inconvénient : on ne maîtrise pas bien l'affichage

Pour afficher ce diagramme dans VScode :

* à gauche aller dans **Extensions** (ou CTRL + SHIFT + X)
* rechercher `mermaid`
  * installer l'extension **Markdown Preview Mermaid Support**
* revenir sur ce fichier
  * faire **CTRL + K**, puis **V**

```mermaid
erDiagram
    UTILISATEUR ||--o{ AUDIT : own
    UTILISATEUR {
        int id PK
        string mot_de_passe
        string name
        string email
    }
    AUDIT ||--|{ FICHIER : contain
    AUDIT {
        int id PK
        int utilisateur_id FK
        date date_audit
        bool statut "default FALSE"
        float(4) score "default NULL"
        numeric(4) emissionCO2 "default NULL"
    }
    FICHIER {
      int id PK
      int audit_id FK
      string code "Not NULL"
      varchar(20) extension "20 caracters max"
      numeric(4) score "default NULL"
      string complexite "default NULL"
      numeric(4) emissionCO2 "default NULL"
    }

```