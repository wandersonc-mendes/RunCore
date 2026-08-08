import hmac

from fastapi import Request
from fastapi.responses import JSONResponse

from config import CLOUDFLARE_ORIGIN_SECRET


ORIGIN_SECRET_HEADER = "X-RunCore-Origin-Secret"
ORIGIN_GUARD_EXEMPT_PATHS = {"/health"}


def origin_request_is_allowed(request: Request) -> bool:
    if not CLOUDFLARE_ORIGIN_SECRET:
        return True

    if request.url.path in ORIGIN_GUARD_EXEMPT_PATHS:
        return True

    received_secret = str(
        request.headers.get(ORIGIN_SECRET_HEADER, "")
    )

    if not received_secret:
        return False

    return hmac.compare_digest(
        received_secret,
        CLOUDFLARE_ORIGIN_SECRET,
    )


async def origin_guard_middleware(request: Request, call_next):
    if origin_request_is_allowed(request):
        return await call_next(request)

    return JSONResponse(
        status_code=403,
        content={
            "detail": "Origem da requisição não autorizada.",
        },
    )
