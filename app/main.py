from fastapi import FastAPI

from app.config import cfg
from app.files.router import router as files_router
from app.register.router import router as register_router

app = FastAPI(
    title=cfg.app_name,
    description=cfg.app_desc,
    version=cfg.app_version,
    debug=cfg.debug,
)
app.include_router(files_router)
app.include_router(register_router)

@app.get("/")
def read_root() -> dict:
    return {"Hello": "World"}
