# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_tables
import logging

from .routers import users, room_types, rooms, services, guests, bookings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name, debug=True)

@app.on_event("startup")
async def on_startup():
    await create_tables()


origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(room_types.router, prefix="/api/room-types", tags=["Room Types"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])
app.include_router(guests.router, prefix="/api/guests", tags=["Guests"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["Bookings"])
