import sqlite3
from datetime import datetime, UTC

DB_PATH = "chat_history.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning TEXT,
                seq INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(chat_id) REFERENCES chats(id)
            )
            """
        )
        conn.commit()

def load_chats_from_db() -> tuple[dict, list]:
    chats = {}
    chat_order = []

    with get_db_connection() as conn:
        rows = conn.execute("SELECT id, title FROM chats ORDER BY updated_at DESC").fetchall()
        for row in rows:
            chat_id = row["id"]
            chat_order.append(chat_id)
            message_rows = conn.execute(
                "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY seq ASC",
                (chat_id,),
            ).fetchall()
            chats[chat_id] = {
                "title": row["title"],
                "messages": [
                    {"role": message["role"], "content": message["content"]}
                    for message in message_rows
                ],
            }

    return chats, chat_order

def save_chat_to_db(chat_id: str, chat: dict) -> None:
    now = datetime.now(UTC).isoformat()

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO chats (id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                updated_at = excluded.updated_at
            """,
            (chat_id, chat["title"], now, now),
        )

        conn.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))

        for seq, message in enumerate(chat["messages"], start=1):
            conn.execute(
                """
                INSERT INTO messages (chat_id, role, content, seq, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chat_id, message["role"], message["content"], seq, now),
            )

        conn.commit()
