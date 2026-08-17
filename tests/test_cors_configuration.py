from main import app


def test_cors_allows_frontend_origin():
    cors_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            cors_middleware = middleware
            break

    assert cors_middleware is not None
    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])
    assert "https://niyantran.blackholeinfiverse.com" in allowed_origins
    assert cors_middleware.kwargs.get("allow_credentials") is False
