from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import LLMUnavailableError


async def llm_unavailable_handler(request: Request, exc: LLMUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"error": "LLM service unavailable", "detail": str(exc)}
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(LLMUnavailableError, llm_unavailable_handler)
