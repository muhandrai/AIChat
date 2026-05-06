# AndroAI - AI Chat Application

Aplikasi chat AI modern yang dibangun dengan FastAPI (Backend) dan React + Vite (Frontend).

## Struktur Project
- `/backend`: API server menggunakan FastAPI dan SQLite.
- `/frontend`: Interface pengguna menggunakan React, Vite, dan Framer Motion.

---

## Prasyarat
Pastikan Anda sudah menginstal:
- [Python 3.10+](https://www.python.org/)
- [Node.js](https://nodejs.org/)

---

## 1. Persiapan Backend
Masuk ke direktori backend dan siapkan virtual environment.

```powershell
# Masuk ke folder backend
cd backend

# Buat virtual environment (jika belum ada)
py -m venv .venv

# Aktifkan virtual environment
.\.venv\Scripts\Activate.ps1

# Instal dependensi
pip install -r requirements.txt
```

### Konfigurasi `.env`
Buat file `.env` di **folder root** project dan tambahkan API Key Anda:
```env
OPENROUTER_API_KEY=your_api_key_here
```

### Menjalankan Backend
```powershell
uvicorn main:app --reload
```
Server akan berjalan di `http://127.0.0.1:8000`.

---

## 2. Persiapan Frontend
Buka terminal baru dan masuk ke direktori frontend.

```powershell
# Masuk ke folder frontend
cd frontend

# Instal dependensi (hanya pertama kali)
npm install

# Jalankan aplikasi
npm run dev
```
Aplikasi akan berjalan di `http://localhost:5173`.

---

## Fitur Utama
- **Real-time Streaming**: Jawaban AI muncul secara streaming menggunakan SSE.
- **File Upload**: Mendukung pembacaan file PDF dan teks.
- **Chat History**: Semua percakapan tersimpan di database lokal (SQLite).
- **Modern UI**: Desain premium dengan animasi halus menggunakan Framer Motion.
