import json
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from redis import RedisError
from utils.mock_llm import ask as llm_ask

from .auth import verify_api_key
from .config import settings
from .cost_guard import check_budget, record_cost, tokens
from .rate_limiter import check_rate_limit
from .redis_client import r, redis_healthy

logger = logging.getLogger("uvicorn.error.agent")
logger.propagate = False
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def log(event: str, **fields):
    logger.info(json.dumps({"event": event, "environment": settings.environment, **fields}))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("startup")
    try:
        yield
    finally:
        r.close()
        log("shutdown")


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, pattern=r"\S")


@app.exception_handler(RedisError)
async def redis_error(request: Request, exc: RedisError):
    return JSONResponse({"detail": "Redis unavailable"}, status_code=503)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not redis_healthy():
        raise HTTPException(503, "Redis unavailable")
    return {"ready": True}


@app.post("/ask")
def ask(body: AskRequest, key: str = Depends(verify_api_key)):
    check_rate_limit(key)
    bucket, reserved = check_budget(body.question)
    try:
        answer = llm_ask(body.question)
    except Exception:
        record_cost(bucket, reserved, 0, 0)
        raise
    record_cost(bucket, reserved, tokens(body.question), tokens(answer))
    log("answer", question_length=len(body.question))
    return {"question": body.question, "answer": answer}
