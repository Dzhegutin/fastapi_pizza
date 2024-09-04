from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import FastAPIUsers

from auth.app import auth_router
from auth.auth import auth_backend
from routes import router
from db import engine, Base

# Создаем FastAPI приложение
app = FastAPI()


# Добавляем CORS middleware (по необходимости)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем все таблицы в базе данных
# Base.metadata.create_all(bind=engine)

# Подключаем маршруты
app.include_router(router, prefix="")
app.include_router(auth_router)
