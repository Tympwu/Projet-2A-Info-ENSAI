# CleanOps

![CI](https://github.com/Tympwu/Projet-2A-Info-ENSAI/actions/workflows/ci.yml/badge.svg)

**CleanOps** is a REST API (with a Streamlit web interface) that automatically audits Python code.
You submit your source files and dependency files; CleanOps checks the security of your
dependencies, estimates the energy footprint of your code, and delivers (or refuses) a
quality certificate.

ENSAI 2nd-year IT project — tutor: Adrien Lacaille.

## :sparkles: Features

| # | Feature | What it does |
| -- | ------- | ------------ |
| F1 | **Cryptographic signature** | Every submission is signed with HMAC-SHA256. The API rejects any submission whose signature is invalid (HTTP 403) before processing it. |
| F2 | **Dependency security audit** | Dependencies are read from `requirements.txt`, `pyproject.toml` and `uv.lock`, then checked against the [OSV](https://osv.dev/) vulnerability database (CVE, CVSS score). The worst vulnerability counts: one critical flaw makes the whole project critical. |
| F3 | **Energy analysis** | The Python AST is parsed to detect energy-hungry anti-patterns (nested loops, recursion) and to estimate the algorithmic complexity O(n^k), the theoretical consumption (kWh) and the emissions (gCO2e). |
| F4 | **SBOM export** | The full inventory of the audited project's components is exported in the standard [CycloneDX 1.6](https://cyclonedx.org/) format. |
| F5 | **History, Quality Gate and signed certificate** | Audits are saved per user. Each audit gets a note out of 20 (security + energy sobriety). A Quality Gate delivers the certificate if the note is above 15/20, or explains why it refuses it. The certificate is signed with RSA, and anyone can check that it is authentic. |

Accepted files: `.py`, `requirements.txt`, `pyproject.toml`, `uv.lock`, and `.zip` archives containing them (50 MB max).


## :arrow_forward: Quick launch with SSP Cloud

Needed: an [SSP Cloud](https://datalab.sspcloud.fr/) account.

### 1. Start the services

- [ ] Launch a **PostgreSQL** service
- [ ] Launch a **VSCode-python** service (Visual Studio Code, Python 3.13, Git)
  - In the *Networking* tab, open ports **5000** (API) and **8000** (web interface)

### 2. Get the project

In the VSCode terminal:

```bash
git clone https://github.com/Tympwu/Projet-2A-Info-ENSAI.git
cd Projet-2A-Info-ENSAI
```

Then open the folder: `File > Open Folder` and choose `Projet-2A-Info-ENSAI`.
:warning: *Projet-2A-Info-ENSAI* must be the root of your Explorer, otherwise the application will not start.

### 3. Install the dependencies

The project uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync --project backend
uv sync --project frontend
```

### 4. Configure the environment

**a) Generate a secret key for the HMAC signature (F1):**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Keep the printed value: the backend and the frontend must use **the same key**.

**b) Generate the RSA key pair used to sign the certificates (F5)** and append it to the `.env` file of step c:

```bash
uv run --project backend python -c "import json; from cryptography.hazmat.primitives.asymmetric import rsa; from cryptography.hazmat.primitives import serialization as s; k = rsa.generate_private_key(public_exponent=65537, key_size=2048); print('PRIVATE_KEY=' + json.dumps(k.private_bytes(s.Encoding.PEM, s.PrivateFormat.PKCS8, s.NoEncryption()).decode())); print('PUBLIC_KEY=' + json.dumps(k.public_key().public_bytes(s.Encoding.PEM, s.PublicFormat.SubjectPublicKeyInfo).decode()))" >> .env
```

Each key is written on **one line**, between double quotes, with `\n` for the line breaks.
Everyone who must verify the same certificates must use the same pair of keys.

**c) Complete the file `.env` at the root of the project.**
The `POSTGRES_*` values are displayed when you click **Open** on your PostgreSQL service in Onyxia.

```default
POSTGRES_HOST=postgresql-cnpg-<suffix>
POSTGRES_PORT=5432
POSTGRES_DATABASE=defaultdb
POSTGRES_USER=user-<username>
POSTGRES_PASSWORD=<password>
POSTGRES_SCHEMA=project

UVICORN_HOST=0.0.0.0
UVICORN_PORT=5000

BACKEND_URL=http://localhost:5000
BACKEND_TIMEOUT=5

HMAC_SECRET_KEY=<the key generated in step a>

PUISSANCE_MACHINE_W=15
INTENSITE_CARBONE_G_KWH=29

PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```

**d) Create the file `frontend/.streamlit/secrets.toml`** with the same HMAC key:

```toml
HMAC_SECRET_KEY = "<the key generated in step a>"
```

:warning: No space inside the quotes. After changing a key, **restart** the backend and the frontend: keys are only read at start-up.

:warning: Never commit `.env` or `secrets.toml`: they contain passwords and secret keys (both are listed in `.gitignore`).

### 5. Launch the application

Open **two terminals**, both at the root of the project:

| Terminal | Command |
| -------- | ------- |
| 1 — API (backend) | `uv run --project backend python backend/src/main.py` |
| 2 — Web interface (frontend) | `cd frontend` then `uv run --project . streamlit run src/app.py` |

:warning: **Do not click on the links displayed in the terminal**: they do not work from your browser.
Go to your [Onyxia services](https://datalab.sspcloud.fr/my-services), click **Open** on the VSCode service,
and use the links for port **8000** (web interface) and port **5000** (API).

:bulb: **First launch:** on the home page, click **Réinitialiser la base de données** (Reset database).
This creates the tables and loads demo data.

Demo accounts:

| Username | Password |
| -------- | -------- |
| `admin` | `admin` |
| `jacques` | `azerty` |
| `jean` | `a` |


## :computer: Using the web interface

1. **Log in** with a demo account or **create an account**. You can also open *nouvel audit* from the sidebar without an account: the audit is then not saved.
2. **Nouvel audit**: drop your files (`.py`, `requirements.txt`, `pyproject.toml`, `uv.lock` or a `.zip`), choose the input size *n* used to estimate the emissions, and click **Lancer l'audit**. The files are signed automatically before being sent.
3. Read the result: status, note out of 20, complexity, emissions and anti-patterns. Download the **certificate** and the **SBOM**.
4. **Vérification de certificats**: upload a certificate (or type its signature, audit id and date) to check that it was really delivered by CleanOps.
5. **Historique**: find all your past audits (logged-in users only).


## :electric_plug: Using the API

Interactive documentation (try every endpoint from your browser): `/docs` or `/redoc` on the API URL.

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/reset_database` | Recreates the tables and loads the demo data |
| `POST` | `/user/` | Creates an account |
| `POST` | `/user/login` | Logs in |
| `GET` `PUT` `DELETE` | `/user/{id}` | Reads, updates or deletes an account |
| `POST` | `/audit/start_audit?nb_entree=500` | Runs an audit on the uploaded files (signed, see below); `nb_entree` is the input size used for the CO2 estimate |
| `GET` | `/audit/` | Lists all audits |
| `GET` `DELETE` | `/audit/{id}` | Reads or deletes an audit |
| `POST` | `/audit/detail_audit?taille_entree=500` | Estimates the CO2 emissions of the last audit |
| `GET` | `/audit/{id}/sbom` | Downloads the SBOM of an audit (CycloneDX JSON) |
| `GET` | `/audit/{id}/certificat` | Applies the Quality Gate and returns the signed certificate (`cle` field) with the reasons for refusal |
| `POST` | `/audit/verif_certificat` | Checks a certificate (`signature`, `id_audit`, `date_delivrance`): returns the audit if it is authentic, 404 otherwise |
| `GET` `DELETE` | `/historic/{user_id}` | Reads or deletes the audit history of a user |
| `GET` | `/file/utilisateur/{user_id}` | Lists the files audited by a user |

### Examples

In the examples, `$API_URL` contains the URL of the API (e.g. `export API_URL=http://localhost:5000`).

```bash
# Log in
curl -X POST "$API_URL/user/login" \
  -H "Content-Type: application/json" \
  -d '{"name": "admin", "mot_de_passe": "admin"}'

# Certificate of audit n°4 (validated in the demo data)
curl "$API_URL/audit/4/certificat"

# SBOM of audit n°4, saved as sbom_audit_4.json
curl -OJ "$API_URL/audit/4/sbom"

# Check a certificate: copy "cle" and "date_delivrance" from the certificate above
curl -X POST "$API_URL/audit/verif_certificat" \
  -H "Content-Type: application/json" \
  -d '{"signature": "<cle>", "id_audit": 4, "date_delivrance": "<date_delivrance>"}'
```

### Submitting files to `/audit/start_audit`

Each submission must carry the header `X-HMAC-Signature`. It is the HMAC-SHA256, computed with
`HMAC_SECRET_KEY`, of a message built from the files sorted by name: for each file,
the length of its name (8 bytes, big-endian), its name, the length of its content (8 bytes, big-endian), its content.

```python
import hashlib, hmac, struct, requests

KEY = "<HMAC_SECRET_KEY>"
files = {"requirements.txt": open("requirements.txt", "rb").read()}

message = b""
for name, data in sorted(files.items()):
    message += struct.pack(">Q", len(name.encode())) + name.encode()
    message += struct.pack(">Q", len(data)) + data
signature = hmac.new(KEY.encode(), message, hashlib.sha256).hexdigest()

response = requests.post(
    "http://localhost:5000/audit/start_audit",
    files=[("liste_fichier", (name, data)) for name, data in files.items()],
    headers={"X-HMAC-Signature": signature},
)
print(response.status_code, response.json())
```


## :file_folder: Project structure

| Item | Description |
| ---- | ----------- |
| `backend/` | REST API (FastAPI), layered architecture — see [backend/README.md](backend/README.md) |
| `frontend/` | Web interface (Streamlit) — see [frontend/README.md](frontend/README.md) |
| `data/` | SQL scripts: `init_db.sql` creates the tables, `pop_db.sql` loads the demo data, `pop_db_test.sql` the test data |
| `doc/` | Report, weekly tracking, UML diagrams |
| `.github/workflows/ci.yml` | Continuous integration pipeline |
| `docker-compose.yml` | Launches the database, the API and the interface with Docker |


## :whale: Quick launch with Docker

Prerequisite: [Docker Desktop](https://docs.docker.com/desktop/).

- [ ] Create the `.env` file of step 4 at the root (only `HMAC_SECRET_KEY`, `PRIVATE_KEY`, `PUBLIC_KEY` and the CO2 settings are needed: the database settings are set in `docker-compose.yml`)
- [ ] Build and start the containers: `docker compose up --build -d`
- [ ] API: http://localhost:5000 — Web interface: http://localhost:8000
- [ ] Stop: `docker compose down`


## :warning: Known limitations

- The complexity is estimated statically from the nesting depth of loops: the code is never executed.
- The energy figures are theoretical (reference machine of 15 W, French electricity mix of 29 gCO2e/kWh). For usual input sizes they are far below 0.01 gCO2e, so the sobriety part of the note only penalises very heavy code.
- Dependencies without a pinned version (e.g. `requests` alone, or found only in `import` statements) are still sent to OSV, which then returns the vulnerabilities of every version of the package: pin your versions in `requirements.txt` or `uv.lock` to avoid false positives.
- The certificate signature covers the audit id and the delivery date; the verification returns the audit as stored in the database, which is the reference for its status and note.
- Software licences (second part of F2) are not analysed: this part was dropped for lack of time.


## :busts_in_silhouette: Team

AOUISSI Junior · CALLET Rémi · CERVANTES Axel · FERRAND Marlène · POUPLIN Timothé
