@echo off
TITLE AndroAI Runner
echo ==========================================
echo    MENYALAKAN APLIKASI ANDROAI
echo ==========================================

:: Build Frontend
echo [+] Membangun Frontend (Building)...
cd frontend
call npm run build
cd ..

:: Menjalankan Backend di jendela baru
echo [+] Memulai Backend (FastAPI)...
start "AndroAI Backend" cmd /k "cd backend && ..\.venv\Scripts\activate && uvicorn main:app --reload"

:: Menjalankan Frontend di jendela yang sama (Preview mode)
echo [+] Memulai Frontend (Preview)...
cd frontend
npm run preview

pause

