"""
memory/conversation.py

Multi-turn conversation memory using LangGraph's SqliteSaver checkpointer.
Each user session gets a unique thread_id so history is isolated per user.

Usage:
    from memory.conversation import get_memory, get_thread_config

    memory = get_memory()
    config = get_thread_config(user_id="user_123")

    # Pass memory + config when compiling and invoking the graph
    app = build_router(memory=memory)
    result = app.invoke(state, config=config)
"""

import uuid
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

# ─── Storage path ─────────────────────────────────────────────────────────────
MEMORY_DIR = Path(__file__).parent
DB_PATH    = MEMORY_DIR / "conversation_history.db"


def get_memory() -> SqliteSaver:
    """
    Returns a LangGraph SqliteSaver checkpointer.
    Creates the memory directory and database file if they don't exist.
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    return SqliteSaver(conn)


def get_thread_config(user_id: str) -> dict:
    """
    Returns a LangGraph config dict scoped to a specific user session.
    Pass this as the second argument to graph.invoke() or graph.stream().

    Args:
        user_id: A unique identifier for the user/session.

    Returns:
        {"configurable": {"thread_id": user_id}}
    """
    return {"configurable": {"thread_id": user_id}}


def generate_user_id() -> str:
    """
    Generate a random unique user/session ID.
    Call once per Streamlit session and store in st.session_state.
    """
    return str(uuid.uuid4())


def get_conversation_history(user_id: str) -> list:
    """
    Retrieve how many checkpoint turns exist for a user.
    Useful for showing session info in the UI.

    Args:
        user_id: The user's thread_id.

    Returns:
        List with turn count dict, or empty list if no history.
    """
    if not DB_PATH.exists():
        return []

    try:
        conn   = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT checkpoint FROM checkpoints WHERE thread_id = ? ORDER BY checkpoint_id ASC",
            (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"turns": len(rows)}] if rows else []
    except sqlite3.OperationalError:
        # Table doesn't exist yet — no history
        return []


def clear_conversation(user_id: str) -> bool:
    """
    Delete all checkpoint history for a specific user.
    Called when user clicks 'Clear history' in the UI.

    Args:
        user_id: The user's thread_id.

    Returns:
        True if successful, False otherwise.
    """
    if not DB_PATH.exists():
        return True

    try:
        conn   = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False