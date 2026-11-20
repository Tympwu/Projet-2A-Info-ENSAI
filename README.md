# CleanOps — Frontend (web interface)

The web interface of CleanOps, built with [Streamlit](https://streamlit.io/).
It does not access the database: everything goes through the backend API.

For installation from scratch, see the [root README](../README.md).


## :rocket: Run

1. Install the dependencies (from the root of the repository): `uv sync --project frontend --all-extras`
2. Create `frontend/.streamlit/secrets.toml` with the same key as `HMAC_SECRET_KEY` in the backend `.env`:

   ```toml
   HMAC_SECRET_KEY = "<your secret key>"
   ```

3. Make sure the backend is running, then launch the interface **from the `frontend` folder**:

   ```bash
   cd frontend
   uv run --project . streamlit run src/app.py
   ```

The interface listens on port **8000** (`.streamlit/config.toml`). On SSP Cloud, open it through the
**Open** button of your VSCode service in Onyxia — not through the link displayed in the terminal.


## :world_map: Pages

| Page | File | Access | What it does |
| ---- | ---- | ------ | ------------ |
| Home | `pages/home.py` | everyone | Log in, go to account creation, reset the database |
| Create account | `pages/creer_compte.py` | everyone | Registration form |
| New audit | `pages/nouvel_audit.py` | everyone (guests: audit not saved) | Upload files, sign them (HMAC), run the audit and display the result |
| CO2 analysis | `pages/analyse_CO2.py` | everyone | Estimate the emissions of the audit for an input size *n* |
| My audits | `pages/historique.py` | logged-in users | History of the user's audits |
| Audit details | `pages/detail_audit.py` | logged-in users | Full result of one audit |

`src/app.py` is the entry point: it redirects to *New audit* if a user is logged in, otherwise to *Home*.


## :classical_building: Architecture

| Item | Role |
| ---- | ---- |
| `src/app.py` | Entry point and redirection |
| `src/pages/` | One file per page |
| `src/utils/api_client.py` | Single client for all calls to the backend (URL and timeout from `BACKEND_URL`, `BACKEND_TIMEOUT`) |
| `src/utils/auth.py` | Session helpers: `exiger_connexion()` protects a page, `deconnecter()` logs out |
| `src/utils/affichage.py` | Shared display of an audit result and page configuration |
| `src/utils/log_init.py` | Logging set-up |
| `src/assets/` | Logo and images |
| `.streamlit/config.toml` | Port and colour theme |
| `.streamlit/secrets.toml` | HMAC key — **never commit it** |

### HMAC signature (F1)

Before sending files to `POST /audit/start_audit`, `nouvel_audit.py` computes an HMAC-SHA256 signature of
the files with the key from `secrets.toml` and sends it in the `X-HMAC-Signature` header.
The backend rejects the submission (HTTP 403) if the signature does not match.


## :hammer_and_wrench: Development

- Logs are written to `frontend/logs/` (format defined in `logging_config.yml`).
- Format and lint with [Ruff](https://docs.astral.sh/ruff/): `uv run --project frontend ruff format frontend/` and `uv run --project frontend ruff check --fix frontend/`
- Format on save is enabled in the workspace (`.vscode/settings.json`).