"""
memory/preferences.py

Persistent user preference store using SQLite.
Tracks what users have searched for, their moods, and content types
so future recommendations can be personalized.

Usage:
    from memory.preferences import PreferenceStore

    prefs = PreferenceStore()
    prefs.save(user_id="user_123", mood="curious", content_type="research", query="transformers")
    history = prefs.get_history(user_id="user_123")
    context = prefs.get_preference_context(user_id="user_123")
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# ─── Storage path ─────────────────────────────────────────────────────────────
MEMORY_DIR = Path(__file__).parent
PREFS_DB   = MEMORY_DIR / "user_preferences.db"

# ─── Schema ───────────────────────────────────────────────────────────────────
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS preferences (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT    NOT NULL,
    timestamp    TEXT    NOT NULL,
    mood         TEXT    DEFAULT '',
    content_type TEXT    DEFAULT '',
    query        TEXT    DEFAULT '',
    route        TEXT    DEFAULT '',
    liked        INTEGER DEFAULT 1
);
"""

CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_user_id ON preferences (user_id);
"""


class PreferenceStore:
    """
    SQLite-backed store for tracking user recommendation history.
    One instance per app session is enough — it's lightweight.
    """

    def __init__(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(PREFS_DB), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row  # allows dict-like access
        self._init_db()

    def _init_db(self):
        cursor = self._conn.cursor()
        cursor.execute(CREATE_TABLE)
        cursor.execute(CREATE_INDEX)
        self._conn.commit()

    def save(
        self,
        user_id:      str,
        mood:         str = "",
        content_type: str = "",
        query:        str = "",
        route:        str = "",
        liked:        bool = True,
    ) -> bool:
        """
        Save a recommendation interaction to the preference store.

        Args:
            user_id:      Unique user/session identifier.
            mood:         Detected mood for this interaction (e.g. "curious").
            content_type: Content type requested (e.g. "leisure_books").
            query:        The search query that was used.
            route:        The route the router selected.
            liked:        Whether the user engaged positively (default True).

        Returns:
            True if saved successfully.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO preferences (user_id, timestamp, mood, content_type, query, route, liked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    datetime.utcnow().isoformat(),
                    mood,
                    content_type,
                    query,
                    route,
                    1 if liked else 0,
                )
            )
            self._conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_history(self, user_id: str, limit: int = 20) -> list:
        """
        Return the most recent interactions for a user.

        Args:
            user_id: Unique user/session identifier.
            limit:   Max number of records to return.

        Returns:
            List of dicts with keys: timestamp, mood, content_type, query, route, liked.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, mood, content_type, query, route, liked
                FROM preferences
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    def get_preference_context(self, user_id: str) -> str:
        """
        Build a short natural-language summary of the user's past preferences.
        Inject this into agent prompts to personalize recommendations.

        Example output:
            "The user has previously enjoyed: research papers (3x), leisure books (2x).
             Common moods: curious, focused. Recent topics: transformers, LLMs."

        Args:
            user_id: Unique user/session identifier.

        Returns:
            A string to inject into LLM prompts, or "" if no history.
        """
        history = self.get_history(user_id, limit=50)
        if not history:
            return ""

        # Count content types
        type_counts: dict = {}
        mood_counts:  dict = {}
        recent_queries = []

        for row in history:
            ct = row.get("content_type", "")
            if ct:
                type_counts[ct] = type_counts.get(ct, 0) + 1

            mood = row.get("mood", "")
            if mood:
                mood_counts[mood] = mood_counts.get(mood, 0) + 1

            q = row.get("query", "")
            if q and q not in recent_queries:
                recent_queries.append(q)

        # Build summary string
        parts = []

        if type_counts:
            types_str = ", ".join(
                f"{k} ({v}x)" for k, v in
                sorted(type_counts.items(), key=lambda x: -x[1])
            )
            parts.append(f"Previously enjoyed: {types_str}")

        if mood_counts:
            moods_str = ", ".join(
                k for k, _ in sorted(mood_counts.items(), key=lambda x: -x[1])[:3]
            )
            parts.append(f"Common moods: {moods_str}")

        if recent_queries:
            topics_str = ", ".join(recent_queries[:5])
            parts.append(f"Recent topics: {topics_str}")

        return ". ".join(parts) + "." if parts else ""

    def get_top_moods(self, user_id: str, top_n: int = 3) -> list:
        """
        Return the user's most frequent moods.
        Useful for the UI to show 'Your usual moods: curious, focused'.

        Args:
            user_id: Unique user/session identifier.
            top_n:   Number of top moods to return.

        Returns:
            List of mood strings ordered by frequency.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT mood, COUNT(*) as cnt
                FROM preferences
                WHERE user_id = ? AND mood != ''
                GROUP BY mood
                ORDER BY cnt DESC
                LIMIT ?
                """,
                (user_id, top_n)
            )
            rows = cursor.fetchall()
            return [row["mood"] for row in rows]
        except sqlite3.Error:
            return []

    def clear(self, user_id: str) -> bool:
        """
        Delete all preference history for a user.

        Args:
            user_id: Unique user/session identifier.

        Returns:
            True if successful.
        """
        try:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
            self._conn.commit()
            return True
        except sqlite3.Error:
            return False

    def close(self):
        """Close the database connection."""
        self._conn.close()