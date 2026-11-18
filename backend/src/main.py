"""
Main entry point for the FastAPI web service.

Initializes logging, loads environment variables, and sets up API routers
for players, login, and games.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse

from controller import (
    audit_controller,
    fichier_controller,
    historique_controller,
    utilisateur_controller,
)
from dao.manager_db import Manager_db
from utils.env_variables import display_values, load_environment_variables
from utils.log_utils import LogMiddleware, get_logger, initialize_logs

logger = get_logger(__name__)

# Initialization
initialize_logs("CleanOps")

load_environment_variables()
display_values()


app = FastAPI(title="CleanOps")

app.add_middleware(LogMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepts Pydantic 422 errors to log them.
    """
    body = await request.body()
    body_str = body.decode() if body else "empty body"

    logger.error(f"Validation Error\nErrors: {exc.errors()}\nBody: {body_str}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body_str},
    )


app.include_router(utilisateur_controller.router, prefix="/user", tags=["Utilisateurs"])
app.include_router(historique_controller.router, prefix="/historic", tags=["Historique"])
app.include_router(audit_controller.router, prefix="/audit", tags=["Audits"])
app.include_router(fichier_controller.router, prefix="/file", tags=["Fichiers"])


@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    """Redirect to the API documentation"""
    return RedirectResponse(url="/docs")


@app.get("/reset_database", tags=["Misc"])
async def reset_database():
    """Reset the database"""
    logger.info("Database reset")
    success = Manager_db().reset_db()

    return {"message": f"Database re-initialization - {'SUCCESS' if success else 'FAILURE'}"}


# Run the FastAPI application
if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("UVICORN_HOST", "127.0.0.1"),
        port=int(os.getenv("UVICORN_PORT", "5000")),
    )

    logger.info("Webservice stopped")
