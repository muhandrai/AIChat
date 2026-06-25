# AndroAI

Aplikasi chat AI dengan dukungan multi-model melalui OpenRouter. Dibangun dengan FastAPI (backend) dan React + Vite (frontend).

## Fitur

- **Multi-Model** — DeepSeek V4 Pro/Flash, Qwen 3.6 Plus, Gemini 2.5 Flash
- **Streaming** — Jawaban AI muncul secara real-time via SSE
- **Reasoning** — Toggle untuk menampilkan proses berpikir model (chain-of-thought)
- **File Upload** — Upload dan baca file PDF atau teks langsung di chat
- **Chat History** — Riwayat percakapan tersimpan di SQLite lokal
- **Auto Title** — Judul chat otomatis di-generate dari respons AI pertama
- **Modern UI** — Animasi halus dengan Framer Motion, markdown rendering, syntax highlighting

## Prasyarat

- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- API Key dari [OpenRouter](https://openrouter.ai/)

## Struktur Project

```
ai-chat/
├── backend/
│   ├── main.py            # FastAPI server & endpoints
│   ├── api_client.py      # OpenRouter streaming client & model config
│   ├── database.py        # SQLite database layer
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/    # ChatWindow, InputBar, Sidebar, dll.
│   │   └── hooks/         # useChat hook
│   ├── package.json
│   └── vite.config.js
├── .env                   # API key (tidak di-commit)
└── README.md
```

## Setup & Menjalankan

### 1. Konfigurasi Environment

Buat file `.env` di **root project**:

```env
OPENROUTER_API_KEY=your_api_key_here
```

### 2. Backend

```powershell
# Buat virtual environment
python -m venv backend/venv

# Aktifkan virtual environment
backend\venv\Scripts\Activate.ps1

# Install dependensi
pip install -r backend/requirements.txt

# Jalankan server
cd backend
uvicorn main:app --reload
```

Backend berjalan di `http://localhost:8000`.

### 3. Frontend

Buka terminal baru:

```powershell
cd frontend

# Install dependensi (pertama kali saja)
npm install

# Jalankan dev server
npm run dev
```

Frontend berjalan di `http://localhost:5173`.

### Catatan

- Jalankan **backend terlebih dahulu**, lalu frontend.
- Kedua server harus berjalan bersamaan di terminal terpisah.
- Vite otomatis mem-proxy request `/api` ke backend di port 8000.

## Model yang Tersedia

| Model | Provider |
|---|---|
| `deepseek/deepseek-v4-pro` | DeepSeek |
| `deepseek/deepseek-v4-flash` | DeepSeek |
| `qwen/qwen3.6-plus` | Alibaba |
| `google/gemini-2.5-flash` | Google Vertex |

Model dapat diubah di `backend/api_client.py` pada variabel `AVAILABLE_MODELS`.

## API Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/models` | Daftar model yang tersedia |
| `GET` | `/api/chats` | Semua chat |
| `POST` | `/api/chats` | Buat chat baru |
| `DELETE` | `/api/chats/{id}` | Hapus chat |
| `GET` | `/api/chats/{id}/messages` | Pesan dalam chat |
| `POST` | `/api/chats/{id}/messages` | Kirim pesan (SSE streaming) |
| `PUT` | `/api/chats/{id}/title` | Update judul chat |
| `POST` | `/api/upload` | Upload file (PDF/teks) |
