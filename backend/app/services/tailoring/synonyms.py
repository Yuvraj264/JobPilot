from typing import Dict, Set

SYNONYM_DICTIONARY: Dict[str, Set[str]] = {
    "qa": {"quality assurance", "software testing", "test engineering"},
    "quality assurance": {"qa", "software testing", "test engineering"},
    "postgres": {"postgresql"},
    "postgresql": {"postgres"},
    "js": {"javascript"},
    "javascript": {"js"},
    "ts": {"typescript"},
    "typescript": {"ts"},
    "py": {"python"},
    "python": {"py"},
}


def get_synonyms(word: str) -> Set[str]:
    w = word.lower().strip()
    return SYNONYM_DICTIONARY.get(w, set())
