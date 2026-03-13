"""
Conftest dla testów Czarne Niebo AI.
Ustawia CN_BASE_DIR na tymczasowy folder żeby testy nie pisały do produkcyjnych danych.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path, monkeypatch):
    """Izoluje testy od produkcyjnych danych — config wskazuje na tmp."""
    monkeypatch.setenv("CN_BASE_DIR", str(tmp_path / "cn_test_data"))
    # Przeładuj config z nowym BASE_DIR
    import importlib
    import czarneniebo.config
    importlib.reload(czarneniebo.config)
    yield
    # Przywróć po teście
    monkeypatch.delenv("CN_BASE_DIR", raising=False)
    importlib.reload(czarneniebo.config)
