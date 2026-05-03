@echo off
TITLE AndroAI Runner
echo ==========================================
echo    MENYALAKAN APLIKASI ANDROAI
echo ==========================================

:: Menjalankan Backend di jendela baru
echo [+] Memulai Backend (FastAPI)...
start "AndroAI Backend" cmd /k "cd backend && ..\.venv\Scripts\activate && uvicorn main:app --reload"

:: Menjalankan Frontend di jendela yang sama
echo [+] Memulai Frontend (Vite)...
cd frontend
npm run dev

pause
