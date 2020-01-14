from fastapi import HTTPException, Query
from starlette.requests import Request
from starlette.responses import JSONResponse

from idunn import settings
from idunn.places import Latlon, place_from_id, InvalidPlaceId
from idunn.utils.rate_limiter import IdunnRateLimiter
from ..directions.client import directions_client


rate_limiter = IdunnRateLimiter(
    resource="idunn.api.directions",
    max_requests=int(settings["DIRECTIONS_RL_MAX_REQUESTS"]),
    expire=int(settings["DIRECTIONS_RL_EXPIRE"]),
)


def get_directions_with_coordinates(
    request: Request,
    # URL values
    f_lon: float,
    f_lat: float,
    t_lon: float,
    t_lat: float,
    # Query parameters
    type: str,
    language: str = "en",
):
    rate_limiter.check_limit_per_client(request)
    from_place = Latlon(f_lat, f_lon)
    to_place = Latlon(t_lat, t_lon)
    if not type:
        raise HTTPException(status_code=400, detail='"type" query param is required')
    return _get_directions_response(from_place, to_place, type, language, request)


def get_directions(
    request: Request,
    origin: str = Query(..., description="Origin place id"),
    destination: str = Query(..., description="Destination place id"),
    type: str = Query(..., description="Transport mode"),
    language: str = Query("en", description="User language"),
):
    rate_limiter.check_limit_per_client(request)
    try:
        from_place = place_from_id(origin)
        to_place = place_from_id(destination)
    except InvalidPlaceId as exc:
        raise HTTPException(status_code=404, detail=exc.message)

    return _get_directions_response(from_place, to_place, type, language, request)


def _get_directions_response(from_place, to_place, type, language, request):
    headers = {"cache-control": "max-age={}".format(settings["DIRECTIONS_CLIENT_CACHE"])}
    return JSONResponse(
        content=directions_client.get_directions(
            from_place, to_place, type, language, params=request.query_params
        ),
        headers=headers,
    )
