import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.db.session import init_db, SessionLocal, engine
from src.db.models import ControlModel
from src.engine.loader import load_controls_from_dir
from src.api.routes.controls import router as controls_router
from src.api.routes.runs import router as runs_router
from src.api.routes.components import router as components_router
from src.api.routes.metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    init_db()

    # Create Views
    views_path = Path("sql/02_views.sql")
    if views_path.exists():
        with open(views_path, "r", encoding="utf-8") as f:
            views_sql = f.read()
        with engine.connect() as conn:
            for stmt in views_sql.split(";"):
                if stmt.strip():
                    try:
                        conn.execute(text(stmt))
                    except Exception:
                        pass
            conn.commit()

    # Preload controls from controls/ directory
    db = SessionLocal()
    try:
        controls_dir = Path("controls")
        if controls_dir.exists():
            loaded_controls = load_controls_from_dir(controls_dir)
            for ctrl in loaded_controls:
                config_hash = ctrl.compute_hash()
                existing = db.query(ControlModel).filter(ControlModel.name == ctrl.name).first()
                if not existing:
                    new_ctrl = ControlModel(
                        name=ctrl.name,
                        version=str(ctrl.version),
                        component=ctrl.component,
                        description=ctrl.description,
                        owner=ctrl.owner,
                        schedule=ctrl.schedule,
                        config_yaml=ctrl.to_yaml(),
                        config_hash=config_hash,
                        enabled=ctrl.enabled
                    )
                    db.add(new_ctrl)
                else:
                    existing.config_yaml = ctrl.to_yaml()
                    existing.config_hash = config_hash
                    existing.description = ctrl.description
            db.commit()
    finally:
        db.close()

    yield
    # Shutdown logic if needed


app = FastAPI(
    title="Control Automation Service",
    description="Enterprise microservice for automated financial reconciliations, data quality controls, and audit trails.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware to enable Excel VBA and Web Client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api/v1
app.include_router(controls_router, prefix="/api/v1")
app.include_router(runs_router, prefix="/api/v1")
app.include_router(components_router, prefix="/api/v1")
app.include_router(metrics_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)