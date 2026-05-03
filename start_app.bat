@echo off
SETLOCAL EnableDelayedExpansion
TITLE AndroAI Runner
echo ==========================================
echo    MENYALAKAN APLIKASI ANDROAI
echo ==========================================

:: Membaca file .env secara robust
if exist .env (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        set "key=%%a"
        set "val=%%b"
        
        :: Bersihkan spasi dari key
        for /f "tokens=1" %%k in ("!key!") do set "key=%%k"
        
        :: Bersihkan tanda kutip dan spasi dari val
        set "val=!val:"=!"
        for /f "tokens=* " %%v in ("!val!") do set "val=%%v"
        
        :: Set variabel ke environment
        set "!key!=!val!"
    )
)

:: Nilai default jika tidak ada di .env
if "%FRONTEND_PORT%"=="" set FRONTEND_PORT=5173
if "%BACKEND_PORT%"=="" set BACKEND_PORT=8000

:: Set environment variable untuk Vite agar terbaca saat build
set VITE_BACKEND_PORT=%BACKEND_PORT%
set VITE_FRONTEND_PORT=%FRONTEND_PORT%

:: Build Frontend
echo [+] Membangun Frontend (Port: %FRONTEND_PORT%, Backend: %BACKEND_PORT%)...
cd frontend
call npm run build
cd ..

:: Menjalankan Backend di jendela baru
echo [+] Memulai Backend (FastAPI di port %BACKEND_PORT%)...
start "AndroAI Backend" cmd /k "cd backend && ..\.venv\Scripts\activate && uvicorn main:app --reload --port %BACKEND_PORT%"

:: Menjalankan Frontend di jendela yang sama (Preview mode)
echo [+] Memulai Frontend (Preview di port %FRONTEND_PORT%)...
cd frontend
npm run preview -- --port %FRONTEND_PORT% --host

pause


