"""
Czarne Niebo AI — konfiguracja globalna
========================================
Wszystkie ścieżki i stałe w jednym miejscu.
Umożliwia instalację na dowolnym komputerze przez zmienną CN_BASE_DIR.

Przykład:
    set CN_BASE_DIR=D:/moje-archiwum
    python -m czarneniebo.web_ui
"""

import os
from pathlib import Path

# ── ścieżki bazowe ────────────────────────────────────────────
# Domyślnie: ~/czarneniebo-data (cross-platform)
# Nadpisz przez: set CN_BASE_DIR=C:/Users/rzecz/AI-Dziennikarstwo
BASE_DIR = Path(os.environ.get(
    "CN_BASE_DIR",
    str(Path.home() / "czarneniebo-data")
))

ARCHIWUM_DIR  = BASE_DIR / "archiwum"
DB_DIR        = BASE_DIR / "archiwum_db"
WYNIKI_DIR    = BASE_DIR / "wyniki"
MODELE_DIR    = BASE_DIR / "modele"

# Utwórz katalogi jeśli nie istnieją
for _d in [ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── modele Ollama ─────────────────────────────────────────────
OLLAMA_MODEL_CHAT = os.environ.get(
    "CN_OLLAMA_MODEL",
    "SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S"
)
OLLAMA_MODEL_EMBED = os.environ.get(
    "CN_OLLAMA_EMBED",
    "bge-m3"          # multilingual, 8K kontekst
)
OLLAMA_MODEL_VISION = os.environ.get(
    "CN_OLLAMA_VISION",
    "moondream"
)

# ── Sentence-Transformers (lokalne embeddingi) ────────────────
# Lżejsza alternatywa: paraphrase-multilingual-MiniLM-L12-v2 (~470MB)
EMBED_MODEL = os.environ.get(
    "CN_EMBED_MODEL",
    "paraphrase-multilingual-mpnet-base-v2"  # ~1.1GB, najlepsza jakość
)

# ── Whisper ───────────────────────────────────────────────────
WHISPER_MODEL  = os.environ.get("CN_WHISPER_MODEL", "medium")
WHISPER_DEVICE = os.environ.get("CN_WHISPER_DEVICE", "cuda")
WHISPER_LANG   = os.environ.get("CN_WHISPER_LANG", "pl")

# ── ChromaDB ──────────────────────────────────────────────────
CHROMA_COLLECTION = "archiwum_dziennikarskie"

# ── Web UI ────────────────────────────────────────────────────
UI_HOST = os.environ.get("CN_UI_HOST", "0.0.0.0")
UI_PORT = int(os.environ.get("CN_UI_PORT", "7860"))

# ── wersja ────────────────────────────────────────────────────
VERSION = "0.1.0"
PROJECT_NAME = "Czarne Niebo AI"
