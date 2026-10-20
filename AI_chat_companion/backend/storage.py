"""
数据持久化：使用 SQLite 数据库（Python 内置 sqlite3，无需额外依赖）。
每个用户独立保存：伴侣名字、选定性格、模型配置方案、聊天历史记录。
数据库文件保存在后端根目录：chat_companion.db
"""
import json
import os
import sqlite3
from typing import Optional

# 数据库文件路径（backend 根目录下）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_companion.db")


def _connect() -> sqlite3.Connection:
    """建立数据库连接（每次操作新建连接，避免多线程共享问题）"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化表结构（应用启动时调用一次）"""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id        TEXT PRIMARY KEY,
                username       TEXT NOT NULL,
                password       TEXT NOT NULL,
                companion_name TEXT NOT NULL,
                persona        TEXT,
                model_config   TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role    TEXT NOT NULL,
                content TEXT NOT NULL,
                time    INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
            """
        )


def _row_to_user(row) -> Optional[dict]:
    """把数据库行转换为用户 dict"""
    if not row:
        return None
    return {
        "user_id": row["user_id"],
        "username": row["username"],
        "password": row["password"],
        "companion_name": row["companion_name"],
        "persona": json.loads(row["persona"]) if row["persona"] else None,
        "model_config": json.loads(row["model_config"]) if row["model_config"] else None,
    }


def create_user(user: dict) -> None:
    """新建用户"""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (user_id, username, password, companion_name, persona, model_config) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                user["user_id"],
                user["username"],
                user["password"],
                user["companion_name"],
                json.dumps(user.get("persona"), ensure_ascii=False) if user.get("persona") else None,
                json.dumps(user.get("model_config"), ensure_ascii=False) if user.get("model_config") else None,
            ),
        )


def get_user(user_id: str) -> Optional[dict]:
    """按用户 ID 读取用户，不存在返回 None"""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return _row_to_user(row)


def update_user(user_id: str, updates: dict) -> Optional[dict]:
    """更新用户字段（persona / model_config 自动 JSON 序列化），不存在返回 None"""
    safe = dict(updates)
    for field in ("persona", "model_config"):
        if field in safe and safe[field] is not None:
            safe[field] = json.dumps(safe[field], ensure_ascii=False)

    set_clause = ", ".join(f"{k} = ?" for k in safe.keys())
    values = list(safe.values()) + [user_id]

    with _connect() as conn:
        cursor = conn.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        if cursor.rowcount == 0:
            return None
    return get_user(user_id)


def user_id_exists(user_id: str) -> bool:
    """判断用户 ID 是否已存在"""
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return row is not None


def append_chat_history(user_id: str, messages: list) -> None:
    """追加聊天记录（messages 为 [{role, content, time}, ...]）"""
    with _connect() as conn:
        conn.executemany(
            "INSERT INTO messages (user_id, role, content, time) VALUES (?, ?, ?, ?)",
            [(user_id, m["role"], m["content"], m.get("time", 0)) for m in messages],
        )


def get_chat_history(user_id: str) -> list:
    """读取某用户的全部聊天记录（按发送时间正序）"""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT role, content, time FROM messages WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"], "time": r["time"]} for r in rows]
