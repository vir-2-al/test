import pytest
from httpx import AsyncClient, ASGITransport, Cookies, Timeout
from fastapi import status
from config import APP_NET_PORT

from main import app

APP_BASE_URL = f"http://localhost:{APP_NET_PORT}"

# Create a Cookies object
cookies = Cookies()
timeout = Timeout(5.0)

@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False),
                           base_url=APP_BASE_URL
                           ) as client:
        global cookies
        response = await client.post(url="api/v1/login",
                                     json={
                                        "username": "test1",
                                        "password": "test1111"
                                    },
                                     timeout=timeout)
        cookies = response.cookies
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_get_users():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False, root_path=''),
                           base_url=APP_BASE_URL
                           ) as client:
        response = await client.get(url="api/v1/users",
                                    cookies=cookies,
                                    timeout=timeout)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_add_user():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False),
                           base_url=APP_BASE_URL
                           ) as client:
        response = await client.post(url="api/v1/users",
                                     json={
                                         "username": "test3",
                                         "password": "test3333"
                                     },
                                     cookies=cookies,
                                     timeout=timeout)
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_logout():
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False),
                           base_url=APP_BASE_URL
                           ) as client:
        response = await client.post(url="api/v1/logout",
                                     cookies=cookies,
                                     timeout=timeout)
        assert response.status_code == status.HTTP_200_OK
