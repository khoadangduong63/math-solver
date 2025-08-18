import logging
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routers import solve

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.log_level.upper())
    ),
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.KeyValueRenderer(
            key_order=["event", "preview", "task", "meta", "to"]
        ),
    ],
)

app = FastAPI(title="Math Solver API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.api_cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(solve.router)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "text_model": settings.llm_text_model,
        "text_provider": settings.llm_text_provider,
        "vision_model": settings.llm_vision_model,
        "vision_provider": settings.llm_vision_provider,
    }
