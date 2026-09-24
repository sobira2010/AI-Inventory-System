"""
Middleware that guarantees CORS headers on error responses.

Why this exists
---------------
Starlette's CORSMiddleware only adds CORS headers to responses that pass
back *through* it. Two error paths bypass it entirely:

1. A route raises an unhandled exception. The outermost ServerErrorMiddleware
   converts it to a bare 500 *outside* the CORS middleware.
2. HTTPException responses with certain status codes may also miss CORS
   headers depending on where they originate.

Either way the browser blocks the response and reports it as a CORS failure
("No 'Access-Control-Allow-Origin' header is present") even though the real
problem is a server error on the endpoint.

This middleware sits OUTSIDE CORSMiddleware (added first in main.py, so it
runs last on the response path). It:
- catches unhandled exceptions, logs the traceback server-side, and returns a
  generic 500 that carries CORS headers for allowed origins
- stamps CORS headers onto any 4xx/5xx response that lacks them

Allowed origins come from the same settings source
(``settings.cors_origins_list``) used by CORSMiddleware, so the two can
never drift apart.

It intentionally does NOT:
- change authentication, database, or AI logic in any way
- expose any server-side error details to the client (tracebacks stay in logs)
- weaken CORS: only configured origins are ever echoed back
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

logger = logging.getLogger(__name__)


class CORSErrorResponseMiddleware(BaseHTTPMiddleware):
    """Attach CORS headers to error responses that bypassed CORSMiddleware."""

    def __init__(self, app):
        super().__init__(app)
        # Resolved once at startup so the check is a fast set lookup per request
        self._allowed_origins = set(settings.cors_origins_list)

    def _stamp_cors_headers(self, request: Request, response: Response) -> None:
        origin = request.headers.get("origin")
        if (
            origin
            and origin in self._allowed_origins
            and "access-control-allow-origin" not in response.headers
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            # Unhandled exception: log the full traceback server-side, return a
            # generic 500 (never leaking internals) that carries CORS headers
            # so the browser can actually read the failure instead of masking
            # it as a CORS error.
            logger.exception(
                "Unhandled exception on %s %s", request.method, request.url.path
            )
            response = Response(
                content=b'{"detail":"Internal Server Error"}',
                status_code=500,
                media_type="application/json",
            )

        if response.status_code >= 400:
            self._stamp_cors_headers(request, response)

        return response
