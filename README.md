
# Hệ thống quản lý khách sạn - FastAPI + PostgreSQL (Docker)

Dự án FastAPI tối giản kết nối với PostgreSQL. Hệ thống quản lý khách sạn hoàn chỉnh với xác thực JWT và quản lý vai trò.

## Yêu cầu hệ thống (Windows 10/macOS + VS Code)
- Python 3.11+
- VS Code + Extensions: *Python*, *Pylance*
- Git (tùy chọn nhưng khuyến nghị)

## 1) Cấu hình môi trường
Sao chép `.env.example` thành `.env` và điều chỉnh các giá trị nếu cần:
```bash
cp .env.example .env
```

## 2) Chuẩn bị PostgreSQL
Tải và cài đặt PostgreSQL, tạo mới database tên `hms`
Schema và seed data sẽ được tạo khi chạy chương trình

## 3) Tạo & kích hoạt virtualenv, cài đặt dependencies
Windows
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
macOS
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4) Chạy API
Windows
```powershell
uvicorn app.main:app --reload
```
macOS
```shell
.venv/bin/uvicorn app.main:app --reload;
```
Ứng dụng sẽ có sẵn tại http://127.0.0.1:8000 (Swagger: http://127.0.0.1:8000/docs).


## 5) Tính năng hệ thống
- **Xác thực JWT**: Mã hoá mật khẩu với bcrypt
- **Quản lý vai trò**: Manager, Receptionist
- **CRUD APIs**: Quản lý phòng, khách, đặt phòng, dịch vụ
- **Cơ sở dữ liệu**: Schema hoàn chỉnh cho hệ thống khách sạn
