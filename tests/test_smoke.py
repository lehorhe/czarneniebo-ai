"""
Smoke testy — Czarne Niebo AI MVP
Sprawdzają czy moduły się importują i kluczowe komponenty działają.
Uruchomienie: pytest tests/ -v

UWAGA: Testy NIE wymagają GPU, modeli Ollama ani spaCy.
Testują strukturę kodu, nie inference.
"""

import os
import sys
import pathlib
import importlib

import pytest


# ── pomocnicze ─────────────────────────────────────────────────

def _can_import(module_name: str) -> bool:
    """Sprawdź czy moduł jest importowalny."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


# ── testy struktury pakietu ────────────────────────────────────

class TestPackageStructure:
    """Sprawdza czy pakiet czarneniebo ma prawidłową strukturę."""

    def test_package_importable(self):
        import czarneniebo
        assert hasattr(czarneniebo, "__version__")
        assert czarneniebo.__version__ == "0.1.0"

    def test_config_importable(self):
        from czarneniebo.config import (
            BASE_DIR, ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR,
            OLLAMA_MODEL_CHAT, WHISPER_MODEL, VERSION,
        )
        assert VERSION == "0.1.0"
        assert isinstance(BASE_DIR, pathlib.Path)

    def test_config_dirs_are_paths(self):
        from czarneniebo.config import ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR
        for d in [ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR]:
            assert isinstance(d, pathlib.Path)

    def test_config_env_override(self, tmp_path, monkeypatch):
        """CN_BASE_DIR powinien nadpisywać domyślną ścieżkę."""
        monkeypatch.setenv("CN_BASE_DIR", str(tmp_path))
        # Przeładuj config
        import czarneniebo.config
        importlib.reload(czarneniebo.config)
        assert czarneniebo.config.BASE_DIR == tmp_path
        # Przywróć
        monkeypatch.delenv("CN_BASE_DIR", raising=False)
        importlib.reload(czarneniebo.config)

    def test_all_modules_exist(self):
        """Sprawdza czy wszystkie pliki .py w czarneniebo/ istnieją."""
        expected = [
            "config", "pipeline", "web_ui", "whisper_transkrypcja",
            "file_watcher", "graf_powiazań", "dezinformacja",
            "restauracja_mediow", "forensics_pipeline",
        ]
        pkg_dir = pathlib.Path(__file__).parent.parent / "czarneniebo"
        for name in expected:
            assert (pkg_dir / f"{name}.py").exists(), f"Brak pliku: czarneniebo/{name}.py"


# ── testy forensics pipeline (bez modeli) ─────────────────────

class TestForensicsPipeline:
    """Testy forensics_pipeline — struktury danych, ELA, metadata."""

    def test_import_dataclasses(self):
        from czarneniebo.forensics_pipeline import (
            Sygnal, ForensicsRaport, ForensicsAnalyzer,
            WAGI_SYGNAŁÓW, PROGI,
        )
        assert "ela" in WAGI_SYGNAŁÓW
        assert sum(WAGI_SYGNAŁÓW.values()) == pytest.approx(1.0, abs=0.01)

    def test_sygnal_creation(self):
        from czarneniebo.forensics_pipeline import Sygnal
        s = Sygnal(nazwa="test", wynik=0.75, pewnosc=0.8, opis="Test OK")
        assert s.wynik == 0.75
        assert s.blad is None

    def test_raport_jako_dict(self):
        from czarneniebo.forensics_pipeline import Sygnal, ForensicsRaport
        s = Sygnal(nazwa="ela", wynik=0.8, pewnosc=0.7, opis="OK")
        r = ForensicsRaport(
            poziom_pewnosci=0.8,
            etykieta="PRAWDOPODOBNIE_AUTENTYCZNY",
            sygnaly={"ela": s},
            zalecenie="Zweryfikuj",
            plik="test.jpg",
            hash_md5="abc123",
        )
        d = r.jako_dict()
        assert d["etykieta"] == "PRAWDOPODOBNIE_AUTENTYCZNY"
        assert "ela" in d["sygnaly"]

    def test_raport_html_generation(self):
        from czarneniebo.forensics_pipeline import Sygnal, ForensicsRaport
        s = Sygnal(nazwa="ela", wynik=0.8, pewnosc=0.7, opis="OK")
        r = ForensicsRaport(
            poziom_pewnosci=0.8,
            etykieta="PRAWDOPODOBNIE_AUTENTYCZNY",
            sygnaly={"ela": s},
            zalecenie="Zweryfikuj",
            plik="test.jpg",
            hash_md5="abc123",
        )
        html = r.html()
        assert "Czarne Niebo AI" in html
        assert "abc123" in html
        assert "PRAWDOPODOBNIE AUTENTYCZNY" in html

    def test_ela_on_real_image(self, tmp_path):
        """ELA na prostym obrazie — powinien zwrócić Sygnal bez błędu."""
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        from PIL import Image

        # Stwórz testowy obraz JPEG
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        img_path = tmp_path / "test.jpg"
        img.save(img_path, format="JPEG", quality=90)

        analyzer = ForensicsAnalyzer()
        sygnal = analyzer._ela(img_path)
        assert sygnal.blad is None
        assert 0.0 <= sygnal.wynik <= 1.0
        assert sygnal.nazwa == "ela"

    def test_metadata_on_image_without_exif(self, tmp_path):
        """Obraz bez EXIF powinien być flagowany."""
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        from PIL import Image

        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img_path = tmp_path / "no_exif.jpg"
        img.save(img_path, format="JPEG")

        analyzer = ForensicsAnalyzer()
        sygnal = analyzer._metadata(img_path)
        # Brak EXIF powinien obniżyć wynik
        assert sygnal.wynik <= 0.6

    def test_analyzer_rejects_unsupported_format(self, tmp_path):
        """Nieobsługiwany format → ValueError."""
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")

        analyzer = ForensicsAnalyzer()
        with pytest.raises(ValueError, match="Nieobsługiwany format"):
            analyzer.analizuj(txt_file)

    def test_analyzer_rejects_missing_file(self):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        analyzer = ForensicsAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analizuj("/nonexistent/file.jpg")


# ── testy dezinformacja ────────────────────────────────────────

class TestDezinformacja:
    """Testy detektora dezinformacji — bez pełnego treningu."""

    @pytest.mark.skipif(not _can_import("sentence_transformers"),
                        reason="sentence-transformers not installed")
    def test_import(self):
        from czarneniebo.dezinformacja import Detektor
        assert Detektor is not None

    @pytest.mark.skipif(not _can_import("sentence_transformers"),
                        reason="sentence-transformers not installed")
    def test_untrained_raises(self):
        """Nienauczone modele powinny rzucać wyjątek."""
        from czarneniebo.dezinformacja import Detektor
        det = Detektor.__new__(Detektor)
        det.wytrenowany = False
        with pytest.raises(RuntimeError, match="nie jest wytrenowany"):
            det.oceń("test")


# ── testy whisper (struktura, bez modelu) ──────────────────────

class TestWhisper:
    @pytest.mark.skipif(not _can_import("faster_whisper"),
                        reason="faster-whisper not installed")
    def test_import(self):
        from czarneniebo.whisper_transkrypcja import transkrybuj, srt_eksport, transkrybuj_folder
        assert callable(transkrybuj)
        assert callable(srt_eksport)

    @pytest.mark.skipif(not _can_import("faster_whisper"),
                        reason="faster-whisper not installed")
    def test_srt_export(self, tmp_path):
        from czarneniebo.whisper_transkrypcja import srt_eksport
        segmenty = [
            {"start": 0.0, "koniec": 2.5, "tekst": "Pierwszy segment"},
            {"start": 2.5, "koniec": 5.0, "tekst": "Drugi segment"},
        ]
        out = tmp_path / "test.srt"
        srt_eksport(segmenty, out)
        content = out.read_text(encoding="utf-8")
        assert "Pierwszy segment" in content
        assert "00:00:00,000 --> 00:00:02,500" in content


# ── testy graf ─────────────────────────────────────────────────

class TestGraf:
    def test_import(self):
        from czarneniebo.graf_powiazań import buduj_graf, wizualizuj, statystyki_grafu
        assert callable(buduj_graf)

    def test_statystyki_pustego_grafu(self):
        import networkx as nx
        from czarneniebo.graf_powiazań import statystyki_grafu
        G = nx.DiGraph()
        stats = statystyki_grafu(G)
        assert stats["wezly"] == 0
        assert stats["krawedzie"] == 0
