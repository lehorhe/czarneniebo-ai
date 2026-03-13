"""
Smoke testy importów — weryfikacja że pakiet czarneniebo jest poprawnie zainstalowany.
Nie wymagają GPU, Ollama ani zewnętrznych usług.
"""
import pytest


def test_pakiet_czarneniebo_importuje():
    import czarneniebo
    assert czarneniebo.__version__ == "0.1.0"
    assert "Lech Rustecki" in czarneniebo.__author__


def test_config_importuje():
    from czarneniebo import config
    assert hasattr(config, "BASE_DIR")
    assert hasattr(config, "ARCHIWUM_DIR")
    assert hasattr(config, "DB_DIR")
    assert hasattr(config, "WYNIKI_DIR")
    assert hasattr(config, "MODELE_DIR")
    assert hasattr(config, "OLLAMA_MODEL_CHAT")
    assert hasattr(config, "OLLAMA_MODEL_EMBED")


def test_forensics_pipeline_importuje():
    from czarneniebo.forensics_pipeline import (
        ForensicsAnalyzer,
        ForensicsRaport,
        Sygnal,
        WAGI_SYGNAŁÓW,
        PROGI,
    )
    # Sprawdź że wagi sumują się do ~1.0
    assert abs(sum(WAGI_SYGNAŁÓW.values()) - 1.0) < 0.001
    assert "autentyczny" in PROGI
    assert "wymaga_weryfikacji" in PROGI


@pytest.mark.skip(reason="Wymaga zainstalowanych zależności core (pdfplumber, spacy, chromadb)")
def test_pipeline_importuje():
    from czarneniebo import pipeline
    assert pipeline


@pytest.mark.skip(reason="Wymaga zainstalowanych zależności core (gradio)")
def test_web_ui_importuje():
    from czarneniebo import web_ui
    assert web_ui
