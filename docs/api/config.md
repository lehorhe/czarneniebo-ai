# czarneniebo.config

Konfiguracja globalna projektu Czarne Niebo AI.

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Stałe konfiguracyjne

```python
BASE_DIR: Path          # Ścieżka bazowa (env: CN_BASE_DIR)
ARCHIWUM_DIR: Path      # Katalog archiwum
DB_DIR: Path            # Katalog bazy ChromaDB
WYNIKI_DIR: Path        # Katalog wyników
MODELE_DIR: Path        # Katalog modeli

OLLAMA_MODEL_CHAT: str  # Model Ollama do czatu (env: CN_OLLAMA_MODEL)
OLLAMA_MODEL_EMBED: str # Model embeddingów (env: CN_OLLAMA_EMBED)
OLLAMA_MODEL_VISION: str # Model wizyjny (env: CN_OLLAMA_VISION)

WHISPER_MODEL: str      # Rozmiar modelu Whisper (env: CN_WHISPER_MODEL)
WHISPER_DEVICE: str     # Urządzenie Whisper (env: CN_WHISPER_DEVICE)
WHISPER_LANG: str       # Język Whisper (env: CN_WHISPER_LANG)

CHROMA_COLLECTION: str  # Nazwa kolekcji ChromaDB
UI_HOST: str            # Host Web UI (env: CN_UI_HOST)
UI_PORT: int            # Port Web UI (env: CN_UI_PORT)
VERSION: str            # Wersja projektu
PROJECT_NAME: str       # Nazwa projektu
```

::: czarneniebo.config
