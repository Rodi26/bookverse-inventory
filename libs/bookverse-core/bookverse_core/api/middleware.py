

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .responses import create_error_response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, header_name: str = "X-Request-ID"):

        super().__init__(app)
        self.header_name = header_name

    async def dispatch(
            self,
            request: Request,
            call_next: Callable) -> Response:

        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers[self.header_name] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):

    def __init__(
        self,
        app,
        log_requests: bool = True,
        log_responses: bool = True,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: list = None
    ):

        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or [
            "/health", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(
            self,
            request: Request,
            call_next: Callable) -> Response:

        if any(request.url.path.startswith(path)
               for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        if self.log_requests:
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(
                    request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get(
                    "user-agent",
                    "unknown"),
            }

            if self.log_request_body and request.method in [
                    "POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        log_data["request_body"] = body.decode("utf-8")[:1000]
                except Exception:
                    pass

            logger.info(f"📥 Request: {log_data}")

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ Request failed: {request_id} {request.method} {request.url.path} "
                f"- {type(e).__name__}: {str(e)} ({duration:.3f}s)")
            raise

        if self.log_responses:
            duration = time.time() - start_time
            log_data = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            }

            if response.status_code >= 500:
                log_level = logging.ERROR
                emoji = "❌"
            elif response.status_code >= 400:
                log_level = logging.WARNING
                emoji = "⚠️"
            else:
                log_level = logging.INFO
                emoji = "📤"

            logger.log(log_level, f"{emoji} Response: {log_data}")

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, include_traceback: bool = False):

        super().__init__(app)
        self.include_traceback = include_traceback

    async def dispatch(
            self,
            request: Request,
            call_next: Callable) -> Response:

        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")

            logger.exception(
                f"❌ Unhandled exception in request {request_id}: {type(e).__name__}: {str(e)}"
            )

            error_details = {
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
            }

            if self.include_traceback:
                import traceback
                error_details["traceback"] = traceback.format_exc()

            error_response = create_error_response(
                error="Internal server error",
                error_code="internal_error",
                details=error_details,
                request_id=request_id
            )

            return JSONResponse(
                status_code=500,
                content=error_response.model_dump()
            )
