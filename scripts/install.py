#!/usr/bin/env python3
"""
Czarne Niebo AI — automatyczny installer
=========================================
Wykrywa GPU/CUDA, tworzy venv, instaluje zależności,
pobiera modele Ollama, testuje instalację.

Użycie:
    python scripts/install.py
    python scripts/install.py --cpu-only
    python scripts/install.py --skip-models
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Windows: wymus UTF-8 na stdout
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).parent.parent.resolve()
VENV_DIR = REPO_ROOT / ".venv"
PYTHON_MIN = (3, 10)
REQUIRED_OLLAMA_MODELS = [
    "SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S",
    "moondream",
]
SPACY_MODEL = "pl_core_news_lg"

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!!]{RESET} {msg}")


def err(msg):
    print(f"{RED}[XX]{RESET} {msg}")


def step(msg):
    print(f"\n{BOLD}-- {msg}{RESET}")


def run(cmd, check=True, capture=False, cwd=None):
    kwargs = dict(cwd=cwd or REPO_ROOT, check=check)
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return subprocess.run(cmd, **kwargs)


def detect_python():
    step("Sprawdzanie Pythona")
    ver = sys.version_info
    if ver < PYTHON_MIN:
        err(f"Python {ver.major}.{ver.minor} — wymagany minimum {PYTHON_MIN[0]}.{PYTHON_MIN[1]}")
        sys.exit(1)
    ok(f"Python {ver.major}.{ver.minor}.{ver.micro}")
    return sys.executable


def detect_gpu():
    step("Wykrywanie GPU / CUDA")
    # Próba przez nvidia-smi
    if shutil.which("nvidia-smi"):
        r = run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader"],
            check=False, capture=True
        )
        if r.returncode == 0:
            info = r.stdout.strip().split("\n")[0]
            ok(f"GPU wykryty: {info}")
            return "cuda"
    warn("nvidia-smi niedostępny — instalacja w trybie CPU")
    return "cpu"


def check_cuda_pytorch(device):
    """Sprawdza czy PyTorch w venv widzi CUDA."""
    py = venv_python()
    if not py.exists():
        return
    r = run(
        [str(py), "-c",
         "import torch; print('cuda' if torch.cuda.is_available() else 'cpu'); "
         "print(torch.version.cuda or 'n/a')"],
        check=False, capture=True
    )
    if r.returncode == 0:
        lines = r.stdout.strip().split("\n")
        torch_device = lines[0] if lines else "?"
        cuda_ver = lines[1] if len(lines) > 1 else "?"
        if torch_device == "cuda":
            ok(f"PyTorch widzi CUDA {cuda_ver}")
        else:
            warn("PyTorch działa w trybie CPU (brak CUDA lub niekompatybilna wersja)")


def venv_python():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def venv_pip():
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def create_venv(python_exe):
    step("Tworzenie wirtualnego środowiska (.venv)")
    if VENV_DIR.exists():
        warn(f".venv już istnieje ({VENV_DIR}) — pomijam tworzenie")
        return
    run([python_exe, "-m", "venv", str(VENV_DIR)])
    ok(f"venv utworzony: {VENV_DIR}")


def install_deps(device):
    step("Instalacja zaleznosci Python")
    py = str(venv_python())
    # Na Windows pip musi byc upgradowany przez python -m pip
    run([py, "-m", "pip", "install", "--upgrade", "pip", "wheel"])

    # PyTorch — odpowiednia wersja dla CUDA/CPU (tylko jesli nie ma)
    r = run([py, "-m", "pip", "show", "torch"], check=False, capture=True)
    if r.returncode == 0:
        ok("PyTorch juz zainstalowany — pomijam")
    elif device == "cuda":
        ok("Instalacja PyTorch z CUDA 12.1 (to moze zajac kilka minut...)")
        run([py, "-m", "pip", "install",
             "torch", "torchvision", "torchaudio",
             "--index-url", "https://download.pytorch.org/whl/cu121"])
    else:
        warn("Instalacja PyTorch CPU-only")
        run([py, "-m", "pip", "install", "torch", "torchvision", "torchaudio",
             "--index-url", "https://download.pytorch.org/whl/cpu"])

    # Core pakiet z opcjonalnymi zaleznosciami premium
    ok("Instalacja czarneniebo-ai[core,premium]")
    run([py, "-m", "pip", "install", "-e", str(REPO_ROOT) + "[core,premium]"])
    ok("Wszystkie zaleznosci zainstalowane")


def install_spacy_model():
    step(f"Instalacja modelu spaCy: {SPACY_MODEL}")
    py = str(venv_python())
    r = run([py, "-m", "spacy", "info", SPACY_MODEL], check=False, capture=True)
    if r.returncode == 0:
        ok(f"{SPACY_MODEL} już zainstalowany")
        return
    run([py, "-m", "spacy", "download", SPACY_MODEL])
    ok(f"{SPACY_MODEL} zainstalowany")


def check_ollama():
    step("Sprawdzanie Ollama")
    if not shutil.which("ollama"):
        warn("Ollama nie znaleziona w PATH")
        print("  Pobierz z: https://ollama.com/download")
        print("  Po instalacji uruchom ponownie ten skrypt lub:")
        print("  ollama pull SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S")
        return False
    r = run(["ollama", "list"], check=False, capture=True)
    if r.returncode != 0:
        warn("Ollama zainstalowana ale nie działa — uruchom serwer Ollama")
        return False
    ok("Ollama dostępna")
    return True


def pull_models(skip):
    step("Pobieranie modeli Ollama")
    if skip:
        warn("--skip-models: pomijam pobieranie modeli")
        return
    if not check_ollama():
        return

    r = run(["ollama", "list"], check=False, capture=True)
    installed = r.stdout if r.returncode == 0 else ""

    for model in REQUIRED_OLLAMA_MODELS:
        short = model.split(":")[0].split("/")[-1]
        if short in installed or model.split(":")[0] in installed:
            ok(f"Model już pobrany: {model}")
        else:
            print(f"  Pobieranie {model} (może zająć kilka minut)...")
            run(["ollama", "pull", model], check=False)
            ok(f"Model pobrany: {model}")


def run_tests():
    step("Uruchamianie testów (bez GPU/Ollama)")
    py = str(venv_python())
    r = run(
        [py, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
        check=False, capture=True
    )
    print(r.stdout[-2000:] if len(r.stdout) > 2000 else r.stdout)
    if r.returncode == 0:
        ok("Wszystkie testy passed")
    else:
        warn("Część testów failed — sprawdź output powyżej")
    return r.returncode == 0


def create_env_file():
    step("Tworzenie pliku .env.example")
    env_example = REPO_ROOT / ".env.example"
    if env_example.exists():
        ok(".env.example już istnieje")
        return
    content = """# Czarne Niebo AI — zmienne środowiskowe
# Skopiuj do .env i dostosuj

# Katalog danych (domyślnie: ~/czarneniebo-data)
# CN_BASE_DIR=D:/moje-archiwum

# Modele Ollama
# CN_OLLAMA_MODEL=SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S
# CN_OLLAMA_EMBED=bge-m3
# CN_OLLAMA_VISION=moondream

# Whisper
# CN_WHISPER_MODEL=medium
# CN_WHISPER_DEVICE=cuda

# Web UI
# CN_UI_HOST=0.0.0.0
# CN_UI_PORT=7860
"""
    env_example.write_text(content, encoding="utf-8")
    ok(".env.example utworzony")


def print_summary(device, tests_ok):
    print(f"\n{'═' * 60}")
    print(f"{BOLD}CZARNE NIEBO AI — INSTALACJA ZAKOŃCZONA{RESET}")
    print(f"{'═' * 60}")
    print(f"  Tryb:      {'GPU (CUDA)' if device == 'cuda' else 'CPU'}")
    print(f"  venv:      {VENV_DIR}")
    if tests_ok is None:
        tests_str = "pominiete (--skip-tests)"
    elif tests_ok:
        tests_str = "[OK] passed"
    else:
        tests_str = "[!!] czesc failed"
    print(f"  Testy:     {tests_str}")
    print()
    print(f"{BOLD}Jak uruchomić:{RESET}")
    if platform.system() == "Windows":
        print(f"  {VENV_DIR}\\Scripts\\python.exe -m czarneniebo.web_ui")
        print(f"  lub: URUCHOM.bat")
    else:
        print(f"  {VENV_DIR}/bin/python -m czarneniebo.web_ui")
    print()
    print(f"  Web UI: http://localhost:7860")
    print(f"{'═' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Czarne Niebo AI installer")
    parser.add_argument("--cpu-only", action="store_true",
                        help="Wymuś instalację CPU (bez CUDA)")
    parser.add_argument("--skip-models", action="store_true",
                        help="Pomiń pobieranie modeli Ollama")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Pomiń testy po instalacji")
    args = parser.parse_args()

    print(f"\n{BOLD}Czarne Niebo AI — Automatyczny Installer{RESET}")
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Repo:   {REPO_ROOT}\n")

    python_exe = detect_python()

    if args.cpu_only:
        device = "cpu"
        warn("Tryb CPU wymuszony (--cpu-only)")
    else:
        device = detect_gpu()

    create_venv(python_exe)
    install_deps(device)
    check_cuda_pytorch(device)
    install_spacy_model()
    create_env_file()
    pull_models(skip=args.skip_models)

    tests_ok = None  # None = skipped
    if not args.skip_tests:
        tests_ok = run_tests()

    print_summary(device, tests_ok)


if __name__ == "__main__":
    main()
