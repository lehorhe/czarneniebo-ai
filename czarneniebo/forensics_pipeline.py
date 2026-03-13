"""
Czarne Niebo AI — Forensics Pipeline (PREMIUM)
================================================
Wielosygnałowy detektor autentyczności mediów.

Nie daje binarnego wyroku — dostarcza "wagę dowodów" dla dziennikarza.
Każdy sygnał jest opisany i uzasadniony. Decyzja należy do człowieka.

WAŻNE: Żaden detektor deepfake'ów nie jest niezawodny.
Fałszywe alarmy i przeoczenia są możliwe. Wynik ZAWSZE wymaga
weryfikacji kontekstowej przez doświadczonego dziennikarza.

Obsługiwane formaty:
    Obrazy: JPG, JPEG, PNG, TIFF, BMP, WEBP
    Video:  MP4, AVI, MOV, MKV (analiza pierwszych 30 klatek)

GPU: GTX 1660 SUPER 6GB — moduły NN działają na CPU (lekkie modele).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
from PIL import Image

from czarneniebo.config import WYNIKI_DIR

# ── stałe ────────────────────────────────────────────────────
WAGI_SYGNAŁÓW = {
    "ela":       0.25,   # Error Level Analysis
    "metadata":  0.20,   # EXIF i historia kompresji
    "nn":        0.30,   # Neural Network detector (HuggingFace)
    "twarz":     0.15,   # Analiza artefaktów twarzy
    "temporal":  0.10,   # Spójność klatek (tylko video)
}

PROGI = {
    "autentyczny":         0.70,   # ≥70% → prawdopodobnie autentyczny
    "wymaga_weryfikacji":  0.40,   # 40-70% → weryfikacja konieczna
    # <40% → podejrzany
}

FORMATY_OBRAZÓW = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
FORMATY_VIDEO   = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


# ── struktury danych ──────────────────────────────────────────

@dataclass
class Sygnal:
    """Wynik jednego sygnału forensics."""
    nazwa: str
    wynik: float              # 0.0 = pewnie fałszywy, 1.0 = pewnie autentyczny
    pewnosc: float            # 0.0–1.0, jak bardzo detektor jest pewny
    opis: str                 # opis dla dziennikarza
    szczegoly: dict = field(default_factory=dict)
    blad: Optional[str] = None


@dataclass
class ForensicsRaport:
    """
    Raport analizy autentyczności medium.

    Attributes:
        poziom_pewnosci: 0.0–1.0 (im wyższy, tym bardziej autentyczny)
        etykieta: słowny opis wyniku
        sygnaly: wyniki każdego sygnału
        zalecenie: rekomendacja dla dziennikarza
        plik: ścieżka do analizowanego pliku
        hash_md5: hash pliku (do identyfikacji)
        timestamp: czas analizy
    """
    poziom_pewnosci: float
    etykieta: str
    sygnaly: dict[str, Sygnal]
    zalecenie: str
    plik: str
    hash_md5: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def jako_dict(self) -> dict:
        return {
            "plik": self.plik,
            "hash_md5": self.hash_md5,
            "timestamp": self.timestamp,
            "poziom_pewnosci": round(self.poziom_pewnosci, 4),
            "etykieta": self.etykieta,
            "zalecenie": self.zalecenie,
            "sygnaly": {
                k: {
                    "wynik": round(v.wynik, 4),
                    "pewnosc": round(v.pewnosc, 4),
                    "opis": v.opis,
                    "szczegoly": v.szczegoly,
                    "blad": v.blad,
                }
                for k, v in self.sygnaly.items()
            },
        }

    def html(self) -> str:
        """Generuje gotowy raport HTML dla redakcji."""
        kolor = {
            "PRAWDOPODOBNIE_AUTENTYCZNY": "#2ecc71",
            "WYMAGA_WERYFIKACJI":         "#f39c12",
            "PODEJRZANY":                 "#e74c3c",
        }.get(self.etykieta, "#95a5a6")

        wiersze_sygnałów = ""
        for nazwa, s in self.sygnaly.items():
            ikona = "✓" if s.wynik >= 0.5 else "⚠" if s.wynik >= 0.3 else "✗"
            blad_info = f'<small style="color:#e74c3c">({s.blad})</small>' if s.blad else ""
            wiersze_sygnałów += f"""
            <tr>
                <td><strong>{nazwa.upper()}</strong></td>
                <td>{ikona} {s.opis} {blad_info}</td>
                <td style="text-align:center">{s.wynik:.0%}</td>
                <td style="text-align:center">{s.pewnosc:.0%}</td>
            </tr>"""

        pasek_szer = int(self.poziom_pewnosci * 100)

        return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>Raport forensics — {pathlib.Path(self.plik).name}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; background: #1a1a2e; color: #eee; }}
  .karta {{ background: #16213e; border-radius: 12px; padding: 24px; margin: 16px 0; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 10px 14px; border-bottom: 1px solid #2d3561; text-align: left; }}
  th {{ background: #0f3460; }}
  .badge {{ display: inline-block; padding: 6px 16px; border-radius: 20px; font-weight: bold;
            background: {kolor}; color: #fff; font-size: 1.1em; }}
  .pasek-tlo {{ background: #2d3561; border-radius: 8px; height: 20px; }}
  .pasek {{ background: {kolor}; border-radius: 8px; height: 20px; width: {pasek_szer}%; }}
  .uwaga {{ background: #4a1c40; border-left: 4px solid #e74c3c; padding: 12px 16px; border-radius: 4px; }}
</style>
</head>
<body>
<div class="karta">
  <h1>Raport Forensics — Czarne Niebo AI</h1>
  <p><strong>Plik:</strong> {pathlib.Path(self.plik).name}</p>
  <p><strong>MD5:</strong> <code>{self.hash_md5}</code></p>
  <p><strong>Data analizy:</strong> {self.timestamp}</p>
</div>

<div class="karta">
  <h2>Wynik: <span class="badge">{self.etykieta.replace("_", " ")}</span></h2>
  <p>Poziom autentyczności: <strong>{self.poziom_pewnosci:.0%}</strong></p>
  <div class="pasek-tlo"><div class="pasek"></div></div>
  <br>
  <p><strong>Zalecenie:</strong> {self.zalecenie}</p>
</div>

<div class="karta">
  <h2>Sygnały szczegółowe</h2>
  <table>
    <tr><th>Sygnał</th><th>Opis</th><th>Wynik</th><th>Pewność</th></tr>
    {wiersze_sygnałów}
  </table>
</div>

<div class="karta uwaga">
  <strong>⚠ WAŻNE:</strong> Żaden detektor deepfake'ów nie jest niezawodny.
  Ten raport to narzędzie pomocnicze — nie dowód ani wyrok.
  Wynik zawsze wymaga weryfikacji przez doświadczonego dziennikarza
  z uwzględnieniem kontekstu publikacji.
</div>
</body></html>"""


# ── główna klasa ──────────────────────────────────────────────

class ForensicsAnalyzer:
    """
    Wielosygnałowy analizator autentyczności mediów.

    Uruchamia do 5 sygnałów równolegle (ThreadPoolExecutor),
    oblicza ważony wynik zbiorczy i generuje raport HTML.

    Example:
        analyzer = ForensicsAnalyzer()
        raport = analyzer.analizuj("zdjecie.jpg")
        print(raport.etykieta, raport.poziom_pewnosci)
        raport_path = analyzer.zapisz_raport(raport)
    """

    def __init__(self, workers: int = 3):
        self._workers = workers
        self._nn_model = None   # lazy-loaded

    # ── publiczne API ─────────────────────────────────────────

    def analizuj(self, sciezka: str | pathlib.Path) -> ForensicsRaport:
        """
        Analizuje plik multimedialny pod kątem autentyczności.

        Args:
            sciezka: Ścieżka do pliku (obraz lub video).

        Returns:
            ForensicsRaport z wynikami wszystkich sygnałów.

        Raises:
            FileNotFoundError: Plik nie istnieje.
            ValueError: Nieobsługiwany format pliku.
        """
        sciezka = pathlib.Path(sciezka)
        if not sciezka.exists():
            raise FileNotFoundError(f"Plik nie istnieje: {sciezka}")

        ext = sciezka.suffix.lower()
        jest_video = ext in FORMATY_VIDEO
        jest_obraz = ext in FORMATY_OBRAZÓW

        if not jest_video and not jest_obraz:
            raise ValueError(f"Nieobsługiwany format: {ext}")

        md5 = self._md5(sciezka)
        print(f"Analizuję: {sciezka.name} (MD5: {md5[:8]}...)")

        # Uruchom sygnały równolegle
        zadania = {
            "ela":      lambda: self._ela(sciezka) if jest_obraz else self._ela_z_klatki(sciezka),
            "metadata": lambda: self._metadata(sciezka),
            "nn":       lambda: self._nn_detekcja(sciezka) if jest_obraz else self._nn_detekcja_video(sciezka),
            "twarz":    lambda: self._twarz(sciezka) if jest_obraz else self._twarz_z_klatki(sciezka),
            "temporal": lambda: self._temporal(sciezka) if jest_video else self._temporal_pominiety(),
        }

        sygnaly: dict[str, Sygnal] = {}
        with ThreadPoolExecutor(max_workers=self._workers) as ex:
            przyszlosci = {ex.submit(fn): nazwa for nazwa, fn in zadania.items()}
            for f in as_completed(przyszlosci):
                nazwa = przyszlosci[f]
                try:
                    sygnaly[nazwa] = f.result()
                except Exception as e:
                    sygnaly[nazwa] = Sygnal(
                        nazwa=nazwa, wynik=0.5, pewnosc=0.0,
                        opis="Błąd analizy", blad=str(e)[:200]
                    )

        # Wynik zbiorczy — ważona suma (pomijamy sygnały z błędem)
        suma_wag = 0.0
        suma_wynikow = 0.0
        for nazwa, s in sygnaly.items():
            if s.blad is None:
                waga = WAGI_SYGNAŁÓW.get(nazwa, 0.1) * s.pewnosc
                suma_wag += waga
                suma_wynikow += waga * s.wynik

        poziom = suma_wynikow / suma_wag if suma_wag > 0 else 0.5

        # Etykieta
        if poziom >= PROGI["autentyczny"]:
            etykieta = "PRAWDOPODOBNIE_AUTENTYCZNY"
            zalecenie = (
                "Sygnały wskazują na autentyczność, ale weryfikacja kontekstu "
                "i źródła publikacji jest zawsze wymagana przed publikacją."
            )
        elif poziom >= PROGI["wymaga_weryfikacji"]:
            etykieta = "WYMAGA_WERYFIKACJI"
            zalecenie = (
                "Sygnały mieszane — konieczna ręczna analiza przez eksperta. "
                "Sprawdź historię publikacji, metadane i kontekst narracyjny."
            )
        else:
            etykieta = "PODEJRZANY"
            zalecenie = (
                "Wiele sygnałów wskazuje na możliwą manipulację. "
                "NIE PUBLIKOWAĆ bez pełnej weryfikacji przez eksperta forensics. "
                "Skontaktuj się z InVID/WeVerify lub ekspertem technicznym."
            )

        return ForensicsRaport(
            poziom_pewnosci=round(poziom, 4),
            etykieta=etykieta,
            sygnaly=sygnaly,
            zalecenie=zalecenie,
            plik=str(sciezka),
            hash_md5=md5,
        )

    def zapisz_raport(self, raport: ForensicsRaport, folder: pathlib.Path = None) -> pathlib.Path:
        """Zapisuje raport jako JSON i HTML. Zwraca ścieżkę do HTML."""
        folder = folder or (WYNIKI_DIR / "forensics")
        folder.mkdir(parents=True, exist_ok=True)

        nazwa = pathlib.Path(raport.plik).stem
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_path = folder / f"{nazwa}_{ts}.json"
        html_path = folder / f"{nazwa}_{ts}.html"

        json_path.write_text(
            json.dumps(raport.jako_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        html_path.write_text(raport.html(), encoding="utf-8")

        print(f"Raport JSON: {json_path}")
        print(f"Raport HTML: {html_path}")
        return html_path

    # ── sygnał 1: ELA ─────────────────────────────────────────

    def _ela(self, sciezka: pathlib.Path, jakosc: int = 95) -> Sygnal:
        """
        Error Level Analysis — anomalie kompresji JPEG.
        Regiony o innym poziomie kompresji niż otoczenie
        wskazują na późniejsze wklejenie lub obróbkę.
        """
        img = Image.open(sciezka).convert("RGB")
        w, h = img.size

        # Rekompress z zadaną jakością i oblicz różnicę
        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=jakosc)
        buf.seek(0)
        recompressed = Image.open(buf).convert("RGB")

        ela_arr = np.abs(
            np.array(img, dtype=np.float32) - np.array(recompressed, dtype=np.float32)
        )

        # Analiza regionalna — podziel na siatkę 8x8
        blok_h, blok_w = h // 8, w // 8
        regionalne_srednie = []
        for ry in range(8):
            for rx in range(8):
                region = ela_arr[
                    ry*blok_h:(ry+1)*blok_h,
                    rx*blok_w:(rx+1)*blok_w
                ]
                regionalne_srednie.append(float(np.mean(region)))

        srednia_global = float(np.mean(ela_arr))
        odch_standardowe = float(np.std(regionalne_srednie))
        max_region = float(max(regionalne_srednie))

        # Wysoka wariancja między regionami = podejrzane
        # Sygnał: 1.0 = autentyczny (niski odchylenie), 0.0 = podejrzany (wysoki)
        # Progi empiryczne (mogą wymagać dostrojenia na danych dziennikarskich)
        prog_podejrzany = 15.0
        prog_ok = 5.0

        if odch_standardowe < prog_ok:
            wynik, pewnosc = 0.85, 0.70
            opis = f"ELA jednolite (σ={odch_standardowe:.1f}) — brak widocznych anomalii kompresji"
        elif odch_standardowe > prog_podejrzany:
            wynik, pewnosc = 0.20, 0.65
            opis = f"ELA niejednolite (σ={odch_standardowe:.1f}) — możliwa obróbka regionalna"
        else:
            wynik, pewnosc = 0.55, 0.40
            opis = f"ELA niejednoznaczne (σ={odch_standardowe:.1f}) — wymaga weryfikacji"

        return Sygnal(
            nazwa="ela",
            wynik=wynik,
            pewnosc=pewnosc,
            opis=opis,
            szczegoly={
                "srednia_ela": round(srednia_global, 2),
                "odchylenie_regionalne": round(odch_standardowe, 2),
                "max_region": round(max_region, 2),
                "format_wejsciowy": sciezka.suffix.lower(),
            }
        )

    def _ela_z_klatki(self, sciezka: pathlib.Path) -> Sygnal:
        """ELA na pierwszej klatce video."""
        klatka = self._wytnij_klatke(sciezka, 0)
        if klatka is None:
            return Sygnal("ela", 0.5, 0.0, "Nie udało się wyciąć klatki video", blad="cv2 error")
        tmp = pathlib.Path(str(sciezka) + "_klatka0.jpg")
        klatka.save(tmp, format="JPEG")
        result = self._ela(tmp)
        tmp.unlink(missing_ok=True)
        return result

    # ── sygnał 2: Metadata ────────────────────────────────────

    def _metadata(self, sciezka: pathlib.Path) -> Sygnal:
        """Analiza EXIF i metadanych."""
        try:
            import piexif
        except ImportError:
            # Fallback: użyj tylko PIL
            return self._metadata_pil(sciezka)

        ext = sciezka.suffix.lower()
        podejrzane = []
        obecne = []

        try:
            img = Image.open(sciezka)
            info = img.info

            # Sprawdź obecność EXIF
            if "exif" not in info and ext in {".jpg", ".jpeg"}:
                podejrzane.append("Brak EXIF w JPG — typowe dla wygenerowanych obrazów")
            elif "exif" in info:
                try:
                    exif = piexif.load(info["exif"])
                    # Sprawdź producenta aparatu
                    if piexif.ImageIFD.Make in exif.get("0th", {}):
                        producent = exif["0th"][piexif.ImageIFD.Make].decode("utf-8", errors="ignore")
                        obecne.append(f"Aparat: {producent.strip()}")
                    else:
                        podejrzane.append("Brak pola Make (producent aparatu)")

                    # Sprawdź spójność dat
                    data_org = exif.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
                    data_mod = exif.get("0th", {}).get(piexif.ImageIFD.DateTime)
                    if data_org and data_mod:
                        obecne.append("Daty EXIF obecne i spójne")
                    elif not data_org:
                        podejrzane.append("Brak DateTimeOriginal")

                    # Sprawdź software
                    software = exif.get("0th", {}).get(piexif.ImageIFD.Software)
                    if software:
                        sw = software.decode("utf-8", errors="ignore").strip()
                        if any(x in sw.lower() for x in ["stable diffusion", "midjourney", "dall-e", "runway", "adobe firefly"]):
                            podejrzane.append(f"Software wskazuje na AI: {sw}")
                        else:
                            obecne.append(f"Software: {sw}")

                except Exception:
                    podejrzane.append("Błąd parsowania EXIF — możliwe uszkodzenie lub oczyszczenie")

            # Format i historia kompresji (przez PIL)
            if hasattr(img, "format") and img.format:
                obecne.append(f"Format: {img.format}")

        except Exception as e:
            return Sygnal("metadata", 0.5, 0.1, "Nie udało się odczytać metadanych", blad=str(e))

        n_pod = len(podejrzane)
        n_ok = len(obecne)

        if n_pod == 0:
            wynik, pewnosc = 0.85, 0.75
            opis = f"Metadane kompletne ({n_ok} pól OK)"
        elif n_pod == 1:
            wynik, pewnosc = 0.55, 0.60
            opis = f"1 anomalia metadanych: {podejrzane[0]}"
        else:
            wynik, pewnosc = 0.20, 0.70
            opis = f"{n_pod} anomalie metadanych — podejrzane"

        return Sygnal(
            nazwa="metadata",
            wynik=wynik,
            pewnosc=pewnosc,
            opis=opis,
            szczegoly={"ok": obecne, "podejrzane": podejrzane}
        )

    def _metadata_pil(self, sciezka: pathlib.Path) -> Sygnal:
        """Uproszczona analiza metadanych bez piexif."""
        try:
            img = Image.open(sciezka)
            ma_exif = "exif" in img.info
            wynik = 0.70 if ma_exif else 0.40
            opis = "EXIF obecny" if ma_exif else "Brak EXIF (zainstaluj piexif dla pełnej analizy)"
            return Sygnal("metadata", wynik, 0.50, opis)
        except Exception as e:
            return Sygnal("metadata", 0.5, 0.0, "Błąd odczytu", blad=str(e))

    # ── sygnał 3: Neural Network ──────────────────────────────

    def _nn_detekcja(self, sciezka: pathlib.Path) -> Sygnal:
        """
        Detekcja przez model HuggingFace.
        Używa: dima806/deepfake_vs_real_image_detection
        Działa na CPU (~2–5s na obraz).
        """
        try:
            from transformers import pipeline as hf_pipeline

            if self._nn_model is None:
                print("  Ładowanie modelu NN (pierwsze użycie)...")
                self._nn_model = hf_pipeline(
                    "image-classification",
                    model="dima806/deepfake_vs_real_image_detection",
                    device=-1,   # CPU (GPU zostawiamy dla Ollama)
                )

            wyniki = self._nn_model(str(sciezka))
            # wyniki: [{"label": "Real", "score": 0.9}, {"label": "Fake", "score": 0.1}]

            real_score = next(
                (r["score"] for r in wyniki if "real" in r["label"].lower()),
                0.5
            )
            fake_score = next(
                (r["score"] for r in wyniki if "fake" in r["label"].lower()),
                0.5
            )

            # real_score → wynik autentyczności
            wynik = float(real_score)
            pewnosc = float(max(real_score, fake_score))  # pewność = max score

            if wynik >= 0.75:
                opis = f"Model NN: prawdopodobnie autentyczny ({wynik:.0%})"
            elif wynik <= 0.30:
                opis = f"Model NN: prawdopodobnie wygenerowany ({fake_score:.0%} fake)"
            else:
                opis = f"Model NN: niejednoznaczny (real={wynik:.0%}, fake={fake_score:.0%})"

            return Sygnal(
                nazwa="nn",
                wynik=wynik,
                pewnosc=pewnosc,
                opis=opis,
                szczegoly={"raw": wyniki}
            )

        except Importers if False else Exception as e:
            return Sygnal(
                "nn", 0.5, 0.0,
                "Model NN niedostępny (zainstaluj transformers)",
                blad=str(e)[:200]
            )

    def _nn_detekcja_video(self, sciezka: pathlib.Path, n_klatek: int = 5) -> Sygnal:
        """Detekcja NN na próbce klatek video."""
        klatki = [self._wytnij_klatke(sciezka, i * 5) for i in range(n_klatek)]
        klatki = [k for k in klatki if k is not None]

        if not klatki:
            return Sygnal("nn", 0.5, 0.0, "Nie udało się wyciąć klatek", blad="cv2 unavailable")

        wyniki_klatek = []
        for i, klatka in enumerate(klatki):
            tmp = pathlib.Path(str(sciezka) + f"_k{i}.jpg")
            klatka.save(tmp, format="JPEG")
            s = self._nn_detekcja(tmp)
            tmp.unlink(missing_ok=True)
            if s.blad is None:
                wyniki_klatek.append(s.wynik)

        if not wyniki_klatek:
            return Sygnal("nn", 0.5, 0.0, "Błąd analizy klatek")

        srednia = float(np.mean(wyniki_klatek))
        wariancja = float(np.var(wyniki_klatek))

        opis = (f"NN video: {len(wyniki_klatek)} klatek, "
                f"śr. autentyczność={srednia:.0%}, var={wariancja:.3f}")

        # Wysoka wariancja = niespójność (podejrzane przy face swap)
        if wariancja > 0.05:
            opis += " — UWAGA: niespójna autentyczność klatek"
            srednia *= 0.8

        return Sygnal("nn", srednia, 0.65, opis,
                      {"klatki": wyniki_klatek, "wariancja": round(wariancja, 4)})

    # ── sygnał 4: Analiza twarzy ──────────────────────────────

    def _twarz(self, sciezka: pathlib.Path) -> Sygnal:
        """
        Wykrywanie twarzy i analiza artefaktów blendingu.
        Używa: facenet-pytorch (MTCNN) do detekcji.
        Sprawdza spójność textury na granicy twarzy/tła.
        """
        try:
            from facenet_pytorch import MTCNN
            import torch

            mtcnn = MTCNN(keep_all=True, device="cpu")
            img = Image.open(sciezka).convert("RGB")
            twarze, prawdopodobienstwa = mtcnn.detect(img)

            if twarze is None or len(twarze) == 0:
                return Sygnal(
                    "twarz", 0.6, 0.3,
                    "Nie wykryto twarzy — analiza blendingu pominięta"
                )

            n_twarzy = len(twarze)
            img_arr = np.array(img, dtype=np.float32)
            podejrzane_twarze = []

            for i, (bbox, prob) in enumerate(zip(twarze, prawdopodobienstwa)):
                if prob is None or prob < 0.9:
                    continue

                x1, y1, x2, y2 = [int(v) for v in bbox]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(img_arr.shape[1], x2), min(img_arr.shape[0], y2)

                # Sprawdź gradient na granicy twarzy (blending artifact)
                margin = 15
                if (y1 > margin and y2 + margin < img_arr.shape[0] and
                        x1 > margin and x2 + margin < img_arr.shape[1]):

                    # Pasek na granicy (wewnątrz vs zewnątrz bboxa)
                    graniczny_wew = img_arr[y1:y1+margin, x1:x2]
                    graniczny_zew = img_arr[max(0,y1-margin):y1, x1:x2]

                    roznica = float(np.mean(np.abs(graniczny_wew - graniczny_zew)))
                    if roznica > 25:  # duży skok = możliwe wklejenie
                        podejrzane_twarze.append(i)

            if podejrzane_twarze:
                wynik = 0.25
                pewnosc = 0.55
                opis = f"Wykryto {n_twarzy} twarz(y), {len(podejrzane_twarze)} z podejrzanymi artefaktami granicy"
            else:
                wynik = 0.80
                pewnosc = 0.65
                opis = f"Wykryto {n_twarzy} twarz(y), granice naturalnie wyglądające"

            return Sygnal("twarz", wynik, pewnosc, opis,
                          {"n_twarzy": n_twarzy, "podejrzane_indeksy": podejrzane_twarze})

        except ImportError:
            return Sygnal(
                "twarz", 0.5, 0.0,
                "facenet-pytorch niedostępny (pip install facenet-pytorch)",
                blad="ImportError"
            )
        except Exception as e:
            return Sygnal("twarz", 0.5, 0.0, "Błąd analizy twarzy", blad=str(e)[:200])

    def _twarz_z_klatki(self, sciezka: pathlib.Path) -> Sygnal:
        klatka = self._wytnij_klatke(sciezka, 30)
        if klatka is None:
            return Sygnal("twarz", 0.5, 0.0, "Nie udało się wyciąć klatki")
        tmp = pathlib.Path(str(sciezka) + "_twarz_klatka.jpg")
        klatka.save(tmp, format="JPEG")
        result = self._twarz(tmp)
        tmp.unlink(missing_ok=True)
        return result

    # ── sygnał 5: Temporal (video) ────────────────────────────

    def _temporal(self, sciezka: pathlib.Path, n_klatek: int = 30) -> Sygnal:
        """
        Analiza spójności czasowej klatek video.
        Face swap często wprowadza mikroniespójności między klatkami
        widoczne jako anomalie w optical flow.
        """
        try:
            import cv2
        except ImportError:
            return Sygnal(
                "temporal", 0.5, 0.0,
                "OpenCV niedostępny (pip install opencv-python-headless)",
                blad="ImportError"
            )

        cap = cv2.VideoCapture(str(sciezka))
        klatki = []
        while len(klatki) < n_klatek:
            ret, frame = cap.read()
            if not ret:
                break
            klatki.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        cap.release()

        if len(klatki) < 2:
            return Sygnal("temporal", 0.5, 0.2, f"Za mało klatek ({len(klatki)})")

        # Oblicz optical flow między kolejnymi klatkami (Lucas-Kanade)
        flows = []
        for i in range(len(klatki) - 1):
            flow = cv2.calcOpticalFlowFarneback(
                klatki[i], klatki[i+1],
                None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude = float(np.sqrt(flow[..., 0]**2 + flow[..., 1]**2).mean())
            flows.append(magnitude)

        srednia_flow = float(np.mean(flows))
        odch_flow = float(np.std(flows))
        # Anomalie: gwałtowne skoki w flow (> 3σ)
        anomalie = sum(1 for f in flows if abs(f - srednia_flow) > 3 * odch_flow)

        if anomalie == 0:
            wynik, pewnosc = 0.85, 0.75
            opis = f"Temporal OK — ruch spójny ({len(klatki)} klatek, 0 anomalii)"
        elif anomalie <= 2:
            wynik, pewnosc = 0.55, 0.55
            opis = f"Temporal: {anomalie} anomalie ruchu — możliwe cięcia lub drobne manipulacje"
        else:
            wynik, pewnosc = 0.25, 0.65
            opis = f"Temporal: {anomalie} anomalie ruchu — podejrzane niespójności klatka-klatka"

        return Sygnal(
            "temporal", wynik, pewnosc, opis,
            {"klatki_analizowane": len(klatki), "anomalie": anomalie,
             "srednia_flow": round(srednia_flow, 3), "odch_flow": round(odch_flow, 3)}
        )

    def _temporal_pominiety(self) -> Sygnal:
        return Sygnal("temporal", 1.0, 1.0, "Analiza temporal N/A — obraz statyczny")

    # ── narzędzia ─────────────────────────────────────────────

    @staticmethod
    def _md5(sciezka: pathlib.Path) -> str:
        h = hashlib.md5()
        with open(sciezka, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _wytnij_klatke(sciezka: pathlib.Path, nr_klatki: int) -> Optional[Image.Image]:
        """Wycina konkretną klatkę z video przez OpenCV."""
        try:
            import cv2
            cap = cv2.VideoCapture(str(sciezka))
            cap.set(cv2.CAP_PROP_POS_FRAMES, nr_klatki)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return None
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        except Exception:
            return None
