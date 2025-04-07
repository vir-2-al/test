APP_NAME = "WEB-APP"
APP_NET_PORT = 8000
APP_ORIGINS = [
    "http://localhost",
    f"http://localhost:{APP_NET_PORT}",
    "http://127.0.0.1",
    f"http://127.0.0.1:{APP_NET_PORT}",
    "null"
]

APP_SECRET_KEY = "INVISIBLE_SECRET_KEY"
APP_COOKIE_NAME = "WEB_APP_COOKIE"

APP_ADMIN_USERNAME = "admin"
APP_ADMIN_PASSWORD = "password"
# DB_SRV_HOST = "localhost"
DB_SRV_HOST = "test_srv_db"

DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@{DB_SRV_HOST}/postgres"