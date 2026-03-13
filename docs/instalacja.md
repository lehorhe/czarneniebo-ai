# Instalacja

## Automatyczna (zalecana)

```bash
git clone https://github.com/czarneniebo/czarneniebo-ai
cd czarneniebo-ai
python scripts/install.py
```

Skrypt automatycznie:
1. Sprawdza Python ≥3.10 i CUDA
2. Tworzy dedykowany venv
3. Instaluje PyTorch z właściwą wersją CUDA
4. Instaluje wszystkie zależności
5. Pobiera model spaCy (`pl_core_news_lg`)
6. Sprawdza Ollama i pobiera potrzebne modele
7. Wypisuje raport ✓/✗

## Ręczna (dla zaawansowanych)

```bash
# 1. Utwórz venv
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# 2. PyTorch z CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 3. Zainstaluj pakiet
pip install -e ".[core]"           # tylko core
pip install -e ".[core,premium]"   # z modułami premium

# 4. Model spaCy
python -m spacy download pl_core_news_lg

# 5. Ollama modele
ollama pull SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S
ollama pull bge-m3
ollama pull moondream
```

## Konfiguracja

Ustaw zmienną środowiskową `CN_BASE_DIR` na folder z archiwum:

=== "Windows"
    ```bat
    set CN_BASE_DIR=D:\moje-archiwum
    ```

=== "Linux/Mac"
    ```bash
    export CN_BASE_DIR=/home/user/archiwum
    ```

=== ".env (opcjonalnie)"
    ```
    CN_BASE_DIR=C:/Users/rzecz/AI-Dziennikarstwo
    CN_OLLAMA_MODEL=SpeakLeash/bielik-11b-v3.0-instruct:IQ3_XXS
    CN_WHISPER_MODEL=medium
    ```

## Uruchomienie

```bash
# Aktywuj venv
venv\Scripts\activate

# Web UI
python -m czarneniebo.web_ui
# → http://localhost:7860

# File Watcher (osobne okno)
python -m czarneniebo.file_watcher
```

## Instalacja na podobnym komputerze (klient)

Wymagania: Windows 10/11, Python 3.10+, NVIDIA GPU z CUDA, Ollama.

```bash
# Jednolinijkowa instalacja (po otrzymaniu dostępu do repo)
git clone https://github.com/[twoja-org]/czarneniebo-ai
cd czarneniebo-ai && python scripts/install.py
```
