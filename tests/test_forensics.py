"""
Testy czarneniebo.forensics_pipeline
Wszystkie testy działają bez GPU, Ollama i internetu.
Używają syntetycznych obrazów generowanych w locie przez PIL.
"""
import io
import pathlib
import tempfile

import numpy as np
import pytest
from PIL import Image


# ── pomocnicze obrazy ────────────────────────────────────────────────────────

def _obraz_jednorodny(width=200, height=200, format="JPEG") -> pathlib.Path:
    """Jednorodny szary obraz — niskie ELA, nie ma twarzy."""
    tmp = tempfile.NamedTemporaryFile(suffix=f".{format.lower()}", delete=False)
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    img.save(tmp.name, format=format)
    return pathlib.Path(tmp.name)


def _obraz_szum(width=200, height=200) -> pathlib.Path:
    """Biały szum — wysoki sygnał ELA (podejrzany)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    arr = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    Image.fromarray(arr).save(tmp.name, format="JPEG", quality=95)
    return pathlib.Path(tmp.name)


# ── testy ForensicsRaport ────────────────────────────────────────────────────

class TestForensicsRaport:
    def test_importuje(self):
        from czarneniebo.forensics_pipeline import ForensicsRaport, Sygnal
        assert ForensicsRaport
        assert Sygnal

    def test_html_zawiera_etykiete(self):
        from czarneniebo.forensics_pipeline import ForensicsRaport, Sygnal
        sygnal = Sygnal(nazwa="ela", wynik=0.8, pewnosc=0.7, opis="OK")
        raport = ForensicsRaport(
            poziom_pewnosci=0.80,
            etykieta="PRAWDOPODOBNIE_AUTENTYCZNY",
            sygnaly={"ela": sygnal},
            zalecenie="Weryfikuj kontekst.",
            plik="test.jpg",
            hash_md5="abc123",
        )
        html = raport.html()
        assert "PRAWDOPODOBNIE AUTENTYCZNY" in html
        assert "abc123" in html
        assert "Czarne Niebo AI" in html

    def test_jako_dict_ma_wszystkie_pola(self):
        from czarneniebo.forensics_pipeline import ForensicsRaport, Sygnal
        sygnal = Sygnal(nazwa="ela", wynik=0.5, pewnosc=0.5, opis="test")
        raport = ForensicsRaport(
            poziom_pewnosci=0.5,
            etykieta="WYMAGA_WERYFIKACJI",
            sygnaly={"ela": sygnal},
            zalecenie="Sprawdź.",
            plik="x.jpg",
            hash_md5="deadbeef",
        )
        d = raport.jako_dict()
        for klucz in ["plik", "hash_md5", "timestamp", "poziom_pewnosci", "etykieta", "sygnaly"]:
            assert klucz in d, f"Brak klucza: {klucz}"

    def test_etykieta_podejrzany(self):
        from czarneniebo.forensics_pipeline import ForensicsRaport, Sygnal
        sygnal = Sygnal(nazwa="nn", wynik=0.1, pewnosc=0.9, opis="Fake")
        raport = ForensicsRaport(
            poziom_pewnosci=0.15,
            etykieta="PODEJRZANY",
            sygnaly={"nn": sygnal},
            zalecenie="NIE PUBLIKOWAĆ.",
            plik="fake.jpg",
            hash_md5="cafebabe",
        )
        html = raport.html()
        assert "#e74c3c" in html  # czerwony kolor dla PODEJRZANY


# ── testy ForensicsAnalyzer — sygnały bez GPU ────────────────────────────────

class TestForensicsAnalyzerSygnaly:
    @pytest.fixture
    def analyzer(self):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        return ForensicsAnalyzer()

    @pytest.fixture
    def img_jednorodny(self):
        p = _obraz_jednorodny()
        yield p
        p.unlink(missing_ok=True)

    @pytest.fixture
    def img_szum(self):
        p = _obraz_szum()
        yield p
        p.unlink(missing_ok=True)

    def test_ela_zwraca_sygnal(self, analyzer, img_jednorodny):
        from czarneniebo.forensics_pipeline import Sygnal
        s = analyzer._ela(img_jednorodny)
        assert isinstance(s, Sygnal)
        assert 0.0 <= s.wynik <= 1.0
        assert 0.0 <= s.pewnosc <= 1.0
        assert s.blad is None

    def test_ela_jednorodny_ma_niski_odchylenie(self, analyzer, img_jednorodny):
        s = analyzer._ela(img_jednorodny)
        # Jednorodny obraz = niski σ → wynik powinien być wysoki (autentyczny)
        assert s.wynik >= 0.5, f"Jednorodny obraz dał wynik {s.wynik} (oczekiwano ≥0.5)"

    def test_metadata_zwraca_sygnal(self, analyzer, img_jednorodny):
        from czarneniebo.forensics_pipeline import Sygnal
        s = analyzer._metadata(img_jednorodny)
        assert isinstance(s, Sygnal)
        assert 0.0 <= s.wynik <= 1.0

    def test_metadata_png_bez_exif(self, analyzer, tmp_path):
        """PNG bez EXIF nie powinien dawać błędu — fallback działa."""
        img_path = tmp_path / "test.png"
        Image.new("RGB", (100, 100), (200, 100, 50)).save(str(img_path), format="PNG")
        s = analyzer._metadata(img_path)
        assert s.blad is None or "EXIF" in s.opis

    def test_temporal_pominiety_dla_obrazu(self, analyzer):
        from czarneniebo.forensics_pipeline import Sygnal
        s = analyzer._temporal_pominiety()
        assert isinstance(s, Sygnal)
        assert s.wynik == 1.0
        assert s.pewnosc == 1.0

    def test_md5_deterministyczny(self, img_jednorodny):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        h1 = ForensicsAnalyzer._md5(img_jednorodny)
        h2 = ForensicsAnalyzer._md5(img_jednorodny)
        assert h1 == h2
        assert len(h1) == 32  # MD5 hex


# ── test pełnej analizy (bez modeli NN) ─────────────────────────────────────

class TestForensicsAnalizaPelna:
    def test_analizuj_obraz_bez_modeli_nn(self, tmp_path):
        """
        Pełna analiza bez zainstalowanych transformers/facenet.
        Sygnały NN i twarz dostaną błąd ImportError,
        ale wynik zbiorczy i tak powinien się obliczyć.
        """
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer, ForensicsRaport

        img_path = tmp_path / "testowy.jpg"
        Image.new("RGB", (300, 300), (100, 150, 200)).save(str(img_path), format="JPEG")

        analyzer = ForensicsAnalyzer()
        raport = analyzer.analizuj(img_path)

        assert isinstance(raport, ForensicsRaport)
        assert 0.0 <= raport.poziom_pewnosci <= 1.0
        assert raport.etykieta in {
            "PRAWDOPODOBNIE_AUTENTYCZNY",
            "WYMAGA_WERYFIKACJI",
            "PODEJRZANY",
        }
        assert raport.hash_md5
        assert len(raport.sygnaly) == 5
        # ELA i metadata zawsze działają (PIL only)
        assert raport.sygnaly["ela"].blad is None
        assert raport.sygnaly["metadata"].blad is None

    def test_analizuj_nieistniajacy_plik_raises(self):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        with pytest.raises(FileNotFoundError):
            ForensicsAnalyzer().analizuj("/nie/istnieje/plik.jpg")

    def test_analizuj_nieobslugiwany_format_raises(self, tmp_path):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        p = tmp_path / "dokument.pdf"
        p.write_bytes(b"%PDF-fake")
        with pytest.raises(ValueError, match="Nieobsługiwany format"):
            ForensicsAnalyzer().analizuj(p)

    def test_zapisz_raport_tworzy_pliki(self, tmp_path):
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer

        img_path = tmp_path / "obraz.jpg"
        Image.new("RGB", (100, 100), (0, 0, 0)).save(str(img_path), format="JPEG")

        analyzer = ForensicsAnalyzer()
        raport = analyzer.analizuj(img_path)
        html_path = analyzer.zapisz_raport(raport, folder=tmp_path / "raporty")

        assert html_path.exists()
        assert html_path.suffix == ".html"
        json_path = html_path.with_suffix(".json")
        assert json_path.exists()
        # JSON musi być parseable
        import json
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["etykieta"] == raport.etykieta
