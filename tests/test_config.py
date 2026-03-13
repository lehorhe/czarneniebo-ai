"""
Testy modułu czarneniebo.config
Nie wymagają GPU, Ollama ani żadnych zewnętrznych usług.
"""
import os
import pathlib

import pytest


def test_config_importuje():
    from czarneniebo import config
    assert config.VERSION == "0.1.0"
    assert config.PROJECT_NAME == "Czarne Niebo AI"


def test_sciezki_sa_pathlib():
    from czarneniebo.config import BASE_DIR, ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR
    for p in [BASE_DIR, ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR]:
        assert isinstance(p, pathlib.Path), f"{p} nie jest pathlib.Path"


def test_sciezki_sa_podkatalogami_base():
    from czarneniebo.config import BASE_DIR, ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR
    for p in [ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR]:
        assert str(p).startswith(str(BASE_DIR)), f"{p} nie jest podkatalogiem {BASE_DIR}"


def test_cn_base_dir_env_override(tmp_path, monkeypatch):
    """CN_BASE_DIR pozwala zmienić ścieżkę bazową bez modyfikacji kodu."""
    monkeypatch.setenv("CN_BASE_DIR", str(tmp_path))
    # Wymagany reimport po zmianie env
    import importlib
    import czarneniebo.config as cfg
    importlib.reload(cfg)
    assert cfg.BASE_DIR == tmp_path
    # Przywróć oryginał po teście
    importlib.reload(cfg)


def test_ollama_modele_sa_stringami():
    from czarneniebo.config import OLLAMA_MODEL_CHAT, OLLAMA_MODEL_EMBED
    assert isinstance(OLLAMA_MODEL_CHAT, str) and len(OLLAMA_MODEL_CHAT) > 0
    assert isinstance(OLLAMA_MODEL_EMBED, str) and len(OLLAMA_MODEL_EMBED) > 0
