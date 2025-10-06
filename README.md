
# Hệ thống quản lý khách sạn - FastAPI + PostgreSQL (Docker)

Dự án FastAPI tối giản kết nối với PostgreSQL qua Docker Compose. Hệ thống quản lý khách sạn hoàn chỉnh với xác thực JWT và quản lý vai trò.

## Yêu cầu hệ thống (Windows 10 + VS Code)
- Python 3.11+
- VS Code + Extensions: *Python*, *Pylance*, *Docker*
- Docker Desktop
- Git (tùy chọn nhưng khuyến nghị)

## 1) Cấu hình môi trường
Sao chép `.env.example` thành `.env` và điều chỉnh các giá trị nếu cần:
```bash
cp .env.example .env
```

## 2) Khởi động PostgreSQL trong Docker
Đặt file SQL hiện có vào `db/init` (ví dụ: `db/init/001_init.sql`). Các file trong thư mục này chạy **một lần** khi tạo cơ sở dữ liệu lần đầu.
Sau đó chạy:
```powershell
docker compose up -d
```

## 3) Tạo & kích hoạt virtualenv, cài đặt dependencies
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4) Chạy API
```powershell
uvicorn app.main:app --reload
```
Ứng dụng sẽ có sẵn tại http://127.0.0.1:8000 (Swagger: http://127.0.0.1:8000/docs).

## 5) Các tác vụ thường dùng
- Dừng DB: `docker compose down`
- Reset dữ liệu DB: `docker compose down -v` (xóa volumes). Sau đó `docker compose up -d` để tạo lại và chạy lại init SQL.
- Kết nối với psql: `docker exec -it postgres-db psql -U app_user -d app_db`

## 6) Ghi chú về seeding
- Bất kỳ file `.sql` nào đặt trong `db/init/` sẽ thực thi theo thứ tự bảng chữ cái **chỉ một lần** khi khởi tạo container lần đầu.
- Nếu thay đổi SQL sau này, xóa volume: `docker compose down -v` để Postgres khởi tạo lại.

## 7) Tính năng hệ thống
- **Xác thực JWT**: Đăng nhập/đăng ký với bcrypt
- **Quản lý vai trò**: Manager, Receptionist, Housekeeping, Accountant
- **CRUD APIs**: Quản lý phòng, khách, đặt phòng, dịch vụ
- **Cơ sở dữ liệu**: Schema hoàn chỉnh cho hệ thống khách sạn
