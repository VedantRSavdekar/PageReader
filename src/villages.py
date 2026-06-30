import os

VILLAGES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "villages.txt")
VILLAGES_PATH = os.path.normpath(VILLAGES_PATH)


def get_villages() -> list:
    """Return the sorted list of known villages."""
    if not os.path.exists(VILLAGES_PATH):
        return []
    with open(VILLAGES_PATH, "r", encoding="utf-8") as f:
        villages = [line.strip() for line in f if line.strip()]
    return sorted(set(villages))


def add_village(name: str):
    """Add a new village to the persistent list if not already present."""
    name = name.strip()
    if not name:
        return
    existing = get_villages()
    if name in existing:
        return
    os.makedirs(os.path.dirname(VILLAGES_PATH), exist_ok=True)
    with open(VILLAGES_PATH, "a", encoding="utf-8") as f:
        f.write(name + "\n")
