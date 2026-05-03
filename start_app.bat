@echo off
TITLE AndroAI Runner
echo ==========================================
echo    MENYALAKAN APLIKASI ANDROAI
echo ==========================================

:: Membaca file .env
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set %%a=%%b
    )
)

:: Pastikan variabel memiliki nilai default jika tidak ada di .env
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5173
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

:: Set environment variable untuk Vite agar terbaca saat build
set VITE_BACKEND_PORT=%BACKEND_PORT%

:: Build Frontend
echo [+] Membangun Frontend (Building dengan VITE_BACKEND_PORT=%VITE_BACKEND_PORT%)...
cd frontend
call npm run build
cd ..

:: Menjalankan Backend di jendela baru
echo [+] Memulai Backend (FastAPI di port %BACKEND_PORT%)...
start "AndroAI Backend" cmd /k "cd backend && ..\.venv\Scripts\activate && uvicorn main:app --reload --port %BACKEND_PORT%"

:: Menjalankan Frontend di jendela yang sama (Preview mode)
echo [+] Memulai Frontend (Preview di port %FRONTEND_PORT%)...
cd frontend
npm run preview -- --port %FRONTEND_PORT%

pause

