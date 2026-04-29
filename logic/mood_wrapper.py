"""
mood_wrapper.py

Maps detected moods to search query hints.
Supports leisure fiction, textbooks, and research paper contexts.
Includes fuzzy matching for LLM outputs that aren't exact mood keywords.
"""

# ---------------------------------------------------------------------------
# Mood → Leisure/Fiction query hints
# ---------------------------------------------------------------------------
MOOD_TO_LEISURE = {
    "sad":          "uplifting fiction OR feel-good fiction",
    "stressed":     "light comedy OR humorous fiction",
    "anxious":      "comfort reads OR cozy mystery OR slice-of-life",
    "lonely":       "heartwarming fiction OR found family",
    "bored":        "thriller OR fast-paced mystery",
    "tired":        "short stories OR novellas OR light reads",
    "happy":        "romcom OR adventurous fiction",
    "excited":      "adventure fiction OR action thriller",
    "adventurous":  "epic fantasy OR travel fiction OR adventure",
    "curious":      "science fiction OR speculative fiction OR historical fiction",
    "focused":      "literary fiction OR slow-burn drama",
    "motivated":    "inspiring fiction OR biographical fiction",
    "nostalgic":    "classic literature OR coming-of-age fiction",
    "romantic":     "romance OR love story",
    "scared":       "horror OR gothic fiction",
    "angry":        "dark fiction OR psychological thriller",
    "hopeful":      "optimistic fiction OR uplifting drama",
    "overwhelmed":  "mindfulness OR simple cozy fiction OR short reads",
}

# ---------------------------------------------------------------------------
# Mood → Textbook/Study context hints
# ---------------------------------------------------------------------------
MOOD_TO_TEXTBOOK = {
    "curious":      "introductory",
    "focused":      "comprehensive advanced",
    "motivated":    "practical hands-on",
    "overwhelmed":  "beginner friendly simplified",
    "excited":      "modern cutting-edge",
    "bored":        "engaging visual interactive",
    "tired":        "concise summary guide",
    "anxious":      "step-by-step structured",
}

# ---------------------------------------------------------------------------
# Mood → Research paper context hints
# ---------------------------------------------------------------------------
MOOD_TO_RESEARCH = {
    "curious":      "survey overview introduction",
    "focused":      "in-depth analysis",
    "motivated":    "applied practical implementation",
    "excited":      "latest recent novel",
    "bored":        "interdisciplinary cross-domain",
    "overwhelmed":  "review tutorial beginner",
}

# ---------------------------------------------------------------------------
# Fuzzy keyword clusters — maps partial LLM outputs to canonical mood keys
# ---------------------------------------------------------------------------
MOOD_ALIASES = {
    "sad":          ["sad", "unhappy", "down", "depressed", "blue", "miserable", "grief", "heartbroken"],
    "stressed":     ["stress", "stressed", "overwhelm", "pressure", "tense", "tension"],
    "anxious":      ["anxi", "nervous", "worried", "worry", "uneasy", "restless"],
    "lonely":       ["lone", "lonely", "isolated", "alone", "miss", "disconnected"],
    "bored":        ["bored", "boring", "dull", "uninterested", "unmotivated"],
    "tired":        ["tired", "exhaust", "fatigue", "sleepy", "drained", "worn"],
    "happy":        ["happy", "joyful", "joy", "great", "good mood", "cheerful", "content"],
    "excited":      ["excit", "thrilled", "enthusiastic", "pumped", "energetic"],
    "adventurous":  ["adventur", "explore", "wander", "travel", "daring"],
    "curious":      ["curio", "wonder", "interested", "intrigue", "fascinated"],
    "focused":      ["focus", "concentrat", "productive", "deep work", "study mode"],
    "motivated":    ["motivat", "inspired", "driven", "ambitious", "determined"],
    "nostalgic":    ["nostalg", "nostalgic", "memories", "reminisce", "old times"],
    "romantic":     ["romantic", "romance", "love", "crush", "affection"],
    "scared":       ["scared", "fear", "afraid", "terrified", "horror"],
    "angry":        ["angry", "anger", "furious", "mad", "frustrated", "rage"],
    "hopeful":      ["hopeful", "hope", "optimistic", "positive", "looking forward"],
    "overwhelmed":  ["overwhelm", "too much", "flooded", "swamped", "overload"],
}


def _resolve_mood(mood: str) -> str:
    """
    Resolve a raw mood string (possibly from LLM) to a canonical mood key.
    First tries exact match, then fuzzy alias match.
    Returns empty string if no match found.
    """
    mood = (mood or "").strip().lower()

    # Exact match first
    if mood in MOOD_TO_LEISURE:
        return mood

    # Fuzzy: check if any alias keyword appears in the mood string
    for canonical, aliases in MOOD_ALIASES.items():
        for alias in aliases:
            if alias in mood:
                return canonical

    return ""


def map_mood_to_query(mood: str, content_type: str = "leisure") -> str:
    """
    Map a mood string to a search query hint.

    Args:
        mood: Raw mood string from LLM (e.g. "feeling very stressed")
        content_type: One of "leisure", "textbook", "research"

    Returns:
        A search query hint string, or "" if no mapping found.
    """
    canonical = _resolve_mood(mood)
    if not canonical:
        return ""

    if content_type == "textbook":
        return MOOD_TO_TEXTBOOK.get(canonical, "")
    elif content_type == "research":
        return MOOD_TO_RESEARCH.get(canonical, "")
    else:
        return MOOD_TO_LEISURE.get(canonical, "")


def get_mood_label(mood: str) -> str:
    """
    Returns the canonical mood label for display purposes.
    Useful for the UI to show 'Detected mood: curious'
    """
    return _resolve_mood(mood) or "unspecified"