#region Import
import os
import mimetypes
from datetime import timedelta
from typing import Annotated
import inspect

import async_logging
import asyncio
import logging
import aiofiles

from fastapi import (FastAPI, Depends, Response, status, Path, APIRouter,
                     HTTPException, UploadFile, File)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete, text, exc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from authx import AuthX, AuthXConfig, TokenPayload

from models import UserLoginScheme, UserInfoScheme
from database import Base, UserModel
from config import (APP_NAME, APP_ORIGINS, APP_SECRET_KEY, APP_COOKIE_NAME, DATABASE_URL, APP_SRV_PORT,
                    APP_ADMIN_USERNAME, APP_ADMIN_PASSWORD)
#endregion

dir_path = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(dir_path + "/files"):
    os.makedirs(dir_path + "/files")
if not os.path.exists(dir_path + "/logs"):
    os.makedirs(dir_path + "/logs")

logger = async_logging.AsyncLogger(
    filename=dir_path + "/logs/file_logs.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

app = FastAPI(title=APP_NAME,
              description="This document describe REST API interface.",
              servers=[{"url": f"http://localhost:{APP_SRV_PORT}"}],
              version="1.0")

config = AuthXConfig()
config.JWT_SECRET_KEY = APP_SECRET_KEY
config.JWT_ACCESS_COOKIE_NAME = APP_COOKIE_NAME
config.JWT_CSRF_METHODS = []
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=20)
config.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=20)
config.JWT_TOKEN_LOCATION = ["cookies"]
auth = AuthX(config=config)
auth.handle_errors(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1 = APIRouter(prefix="/api/v1", tags=["Common"])
api_v1_users = APIRouter(prefix="/api/v1/users", tags=["Users"])
api_v1_files = APIRouter(prefix="/api/v1/files", tags=["Files"])

app.mount("/files", StaticFiles(directory="files"), name="files")

engine = create_async_engine(DATABASE_URL, echo=True)
new_session = async_sessionmaker(bind=engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

#region Common
@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")

@api_v1.post("/init_db",
             dependencies=[Depends(auth.access_token_required)],
             summary="Prepare database")
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await logger.info(__name__ + "." + inspect.stack()[0][3])
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("INSERT INTO users (id, username, password) VALUES(:id, :username, :password) ON CONFLICT DO NOTHING"),
            {"id": 0, "username": APP_ADMIN_USERNAME, "password": APP_ADMIN_PASSWORD},
        )

@api_v1.post("/login",
             status_code=status.HTTP_200_OK,
             summary="User authorization")
async def login(data: UserLoginScheme,
                session: SessionDep,
                response: Response):
    query = select(UserModel).where(UserModel.username == data.username, UserModel.password == data.password)
    result = await session.execute(query)
    user = result.scalars().first()
    if user:
        token = auth.create_access_token(uid=str(user.id))
        response.delete_cookie(key=config.JWT_ACCESS_COOKIE_NAME)
        response.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME, value=token)
        await logger.info(__name__ + "." + inspect.stack()[0][3] + f": username: {data.username}")
        return {"message": "Login successful"}
    else:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": Invalid credentials for {data.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@api_v1.post("/logout",
             summary="User authorization",
             status_code=status.HTTP_200_OK,
             dependencies=[Depends(auth.access_token_required)])
async def logout(response: Response,
                 payload: TokenPayload = Depends(auth.access_token_required)):
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {payload.sub}")

    response.delete_cookie(key=config.JWT_ACCESS_COOKIE_NAME)
    return {"message": "Logout successful"}
#endregion

#region Users
@api_v1_users.post("",
             summary="Add new user",
             status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(auth.access_token_required)])
async def add_user(data: UserLoginScheme,
                   session: SessionDep,
                   payload: TokenPayload = Depends(auth.access_token_required)):
    new_user = UserModel(
        username = data.username,
        password = data.password,
    )
    try:
        session.add(new_user)
        await session.commit()
        await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {payload.sub} create username: {data.username}")
        return {"message": "User created"}
    except exc.SQLAlchemyError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed execute. Message: {e}.!")

@api_v1_users.delete("/{uid}",
               summary="Delete user (available only for current user)",
               status_code=status.HTTP_200_OK,
               dependencies=[Depends(auth.access_token_required)])
async def del_user(session: SessionDep,
                   response: Response,
                   uid: int = Path(ge=0, description="User ID"),
                   payload: TokenPayload = Depends(auth.access_token_required)):
    current_uid = int(payload.sub)
    if current_uid != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrent credentials")
    try:
        query = delete(UserModel).where(UserModel.id == uid)
        await session.execute(query)
        await session.commit()
        await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {uid}")
        response.delete_cookie(key=config.JWT_ACCESS_COOKIE_NAME)
        return {"message": "User deleted"}
    except exc.SQLAlchemyError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed execute. Message: {e}.!")


@api_v1_users.get("",
            summary="Get all users",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(auth.access_token_required)])
async def get_users(session: SessionDep,
                    payload: TokenPayload = Depends(auth.access_token_required)):
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {payload.sub}")
    try:
        query = select(UserModel)
        result = await session.execute(query)
        return {"users": result.scalars().all()}
    except exc.SQLAlchemyError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed execute. Message: {e}.!")


@api_v1_users.get("/{uid}",
            summary="Get user info by ID (available only for current user)",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(auth.access_token_required)])
async def get_user_info(session: SessionDep,
                        uid: int = Path(ge=0, description="User ID"),
                        payload: TokenPayload = Depends(auth.access_token_required)) -> UserInfoScheme:
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {uid}")
    current_uid = int(payload.sub)
    if current_uid != uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrent credentials")
    try:
        query = select(UserModel).where(UserModel.id == uid)
        result = await session.execute(query)
        user = result.scalars().first()
        if user:
            return user
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except exc.SQLAlchemyError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed execute. Message: {e}")

@api_v1_users.put("/{uid}",
            summary="Update user information (available only for current user)",
            status_code=status.HTTP_200_OK,
            dependencies=[Depends(auth.access_token_required)])
async def set_user_info(data: UserInfoScheme,
                        session: SessionDep,
                        payload: TokenPayload = Depends(auth.access_token_required)):
    current_uid = int(payload.sub)
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {current_uid}")
    if current_uid != data.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrent credentials")

    user = await session.get(UserModel, data.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # print(UserInfoScheme.model_validate(user).model_dump())
    user.username = data.username
    user.password = data.password
    user.first_name = data.first_name
    user.middle_name = data.middle_name
    user.last_name = data.last_name
    user.company = data.company
    user.job_title = data.job_title
    try:
        await session.commit()
        await logger.info(__name__ + "." + inspect.stack()[0][3] + f": uid: {payload.sub} update username: {data.username}")
        return {"message": "User updated"}
    except exc.SQLAlchemyError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed execute. Message: {e}")
#endregion

#region Files
@api_v1_files.get("",
                  summary="Get all files for current user",
                  status_code=status.HTTP_200_OK,
                  dependencies=[Depends(auth.access_token_required)])
async def get_files(payload: TokenPayload = Depends(auth.access_token_required)):
    await logger.info(__name__ + "." + inspect.stack()[0][3])
    try:
        uid = payload.sub
        user_path = f"files/{uid}"
        if not os.path.exists(user_path):
            return {"files": []}
        files = sorted(os.listdir(user_path))
        return {"files": files}
    except OSError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"message": str(e)}) from e

@api_v1_files.post("",
                   summary="Upload files",
                   status_code=status.HTTP_201_CREATED,
                   dependencies=[Depends(auth.access_token_required)])
async def upload_files(files: list[UploadFile] = File(...), payload: TokenPayload = Depends(auth.access_token_required)):
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": files: {files}")
    try:
        uid = payload.sub
        for file in files:
            file_location = f"files/{uid}/{file.filename}"
            if not os.path.exists(f"files/{uid}"):
                os.makedirs(f"files/{uid}")
            async with aiofiles.open(file_location, "wb") as buffer:            # with open(file_location, "wb") as buffer:
                await buffer.write(await file.read())                                 #     buffer.write(await file.read())

        return {"message": "Files uploaded successfully"}
    except OSError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"message": str(e)}) from e

async def chunk_file(filename: str):
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": filename: {filename}")
    try:
        CHUNK_SIZE = 1 * 1024 * 1024        # = 1MB - default chunk size
        async with aiofiles.open(filename, "rb") as file:
            while chunk := await file.read(CHUNK_SIZE):
                yield chunk

    except OSError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")

@api_v1_files.get("/{filename}",
                  summary="Download files",
                  dependencies=[Depends(auth.access_token_required)])
async def download_file(filename: str = Path(min_length=1, max_length=255, description="File name"),
                        payload: TokenPayload = Depends(auth.access_token_required)):
    await logger.info(__name__ + "." + inspect.stack()[0][3] + f": filename: {filename}")
    try:
        uid = payload.sub
        full_path_name = f"files/{uid}/{filename}"
        if not os.path.isfile(full_path_name):
            return HTTPException(status.HTTP_404_NOT_FOUND)
        media_type, _ = mimetypes.guess_type(full_path_name)
        return StreamingResponse(chunk_file(full_path_name), media_type=media_type)
    except OSError as e:
        await logger.error(__name__ + "." + inspect.stack()[0][3] + f": {e}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail={"message": str(e)}) from e
#endregion

@app.on_event("startup")
async def startup_database():
    await logger.info(__name__ + "." + inspect.stack()[0][3])

@app.on_event("shutdown")
async def shutdown_database():
    await logger.info(__name__ + "." + inspect.stack()[0][3])

app.include_router(api_v1)
app.include_router(api_v1_users)
app.include_router(api_v1_files)

async def main():
    import uvicorn

    await logger.info(__name__ + "." + inspect.stack()[0][3] + ": start")
    mimetypes.init()
    await init_db()
    uvicorn.run("main:app", host="0.0.0.0", port=APP_SRV_PORT,
                workers=1, reload=True, headers=[("server", "x-server")]
                )

if __name__ == "__main__":
    asyncio.run(main())
