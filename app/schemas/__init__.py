from .user import UserCreate, UserUpdate, UserOut, UserLogin
from .auth import LoginRequest, RegisterRequest, Token as AuthToken, UserOut as AuthUserOut
from .room_type import RoomTypeCreate, RoomTypeUpdate, RoomTypeOut
from .service import ServiceCreate, ServiceUpdate, ServiceOut
from .room import RoomCreate, RoomUpdate, RoomOut
from .guest import GuestCreate, GuestUpdate, GuestOut
from .booking import BookingCreate, BookingUpdate, BookingOut
from .booking_detail import BookingDetailCreate, BookingDetailUpdate, BookingDetailOut
from .payment import PaymentCreate, PaymentUpdate, PaymentOut

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserOut", "UserLogin", "Token",
    # Auth schemas
    "LoginRequest", "RegisterRequest", "AuthToken", "AuthUserOut",
    # Room Type schemas
    "RoomTypeCreate", "RoomTypeUpdate", "RoomTypeOut",
    # Service schemas
    "ServiceCreate", "ServiceUpdate", "ServiceOut",
    # Room schemas
    "RoomCreate", "RoomUpdate", "RoomOut",
    # Guest schemas
    "GuestCreate", "GuestUpdate", "GuestOut",
    # Booking schemas
    "BookingCreate", "BookingUpdate", "BookingOut",
    # Booking Detail schemas
    "BookingDetailCreate", "BookingDetailUpdate", "BookingDetailOut",
    # Payment schemas
    "PaymentCreate", "PaymentUpdate", "PaymentOut",
]