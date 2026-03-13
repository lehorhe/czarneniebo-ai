"""
Transkrypcja audio/video — faster-whisper
GPU: GTX 1660 SUPER 6.4GB

Model "medium" mieści się w ~3GB VRAM, zostawiając margines na inne zadania.
Dla nagrań z lat 80-90 z szumem taśmowym: word_timestamps=True i vad_filter=True.
"""

import pathlib
from faster_whisper import WhisperModel

# ── ładowanie modelu ──────────────────────────────────────────
# device="cuda", compute_type="int8" → optymalnie dla GTX 1660 6GB
# Zmień na device="cpu", compute_type="int8" jeśli VRAM zajęty przez inne modele
_model = None


def zaladuj_model(rozmiar: str = "medium", urzadzenie: str = "cuda"):
    """Lazy-load modelu Whisper."""
    global _model
    if _model is None:
        print(f"Ładowanie Whisper {rozmiar} na {urzadzenie}...")
        _model = WhisperModel(rozmiar, device=urzadzenie, compute_type="int8")
        print("Whisper gotowy.")
    return _model


def transkrybuj(
    sciezka_audio: str | pathlib.Path,
    jezyk: str = "pl",
    rozmiar: str = "medium",
    urzadzenie: str = "cuda",
    znaczniki_czasu: bool = True,
    filtr_ciszy: bool = True,
) -> dict:
    """
    Transkrybuje plik audio/video do tekstu.

    Args:
        sciezka_audio: Ścieżka do pliku (mp3, mp4, wav, ogg, m4a, ...)
        jezyk: Kod języka — "pl" dla polskiego, None = autodetekcja
        rozmiar: Rozmiar modelu Whisper ("tiny", "base", "small", "medium", "large-v3")
        urzadzenie: "cuda" lub "cpu"
        znaczniki_czasu: Czy dołączyć timestampy do segmentów
        filtr_ciszy: VAD — pomija ciszę, poprawia nagrania archiwalne

    Returns:
        dict z kluczami: tekst, segmenty, jezyk, dlugosc_s
    """
    model = zaladuj_model(rozmiar, urzadzenie)
    sciezka = pathlib.Path(sciezka_audio)

    print(f"Transkrybuję: {sciezka.name}")
    segmenty, info = model.transcribe(
        str(sciezka),
        language=jezyk,
        word_timestamps=znaczniki_czasu,
        vad_filter=filtr_ciszy,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    wynik_segmenty = []
    pelny_tekst = []

    for seg in segmenty:
        pelny_tekst.append(seg.text.strip())
        wynik_segmenty.append({
            "start": round(seg.start, 2),
            "koniec": round(seg.end, 2),
            "tekst": seg.text.strip(),
        })

    tekst = " ".join(pelny_tekst)
    print(f"Gotowe — {len(tekst)} znaków, {len(wynik_segmenty)} segmentów")
    print(f"Wykryty język: {info.language} (pewność: {info.language_probability:.0%})")

    return {
        "tekst": tekst,
        "segmenty": wynik_segmenty,
        "jezyk": info.language,
        "pewnosc_jezyka": info.language_probability,
        "dlugosc_s": wynik_segmenty[-1]["koniec"] if wynik_segmenty else 0,
    }


def transkrybuj_folder(
    folder: str | pathlib.Path,
    rozszerzenia: set = {".mp3", ".mp4", ".wav", ".ogg", ".m4a", ".flac"},
    jezyk: str = "pl",
) -> list[dict]:
    """Transkrybuje wszystkie pliki audio/video w folderze."""
    folder = pathlib.Path(folder)
    pliki = [p for p in folder.rglob("*") if p.suffix.lower() in rozszerzenia]
    print(f"Znaleziono {len(pliki)} plików audio/video")

    wyniki = []
    for p in pliki:
        wynik = transkrybuj(p, jezyk=jezyk)
        wynik["plik"] = p.name
        wyniki.append(wynik)

        # Zapisz transkrypcję jako TXT obok oryginału
        txt_path = p.with_suffix(".transkrypcja.txt")
        txt_path.write_text(wynik["tekst"], encoding="utf-8")
        print(f"  Zapisano: {txt_path.name}")

    return wyniki


def srt_eksport(segmenty: list[dict], wyjscie: str | pathlib.Path) -> None:
    """Eksportuje transkrypcję w formacie SRT (napisy)."""
    def czas_srt(s: float) -> str:
        h, rem = divmod(int(s), 3600)
        m, sec = divmod(rem, 60)
        ms = int((s - int(s)) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    with open(wyjscie, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segmenty, 1):
            f.write(f"{i}\n")
            f.write(f"{czas_srt(seg['start'])} --> {czas_srt(seg['koniec'])}\n")
            f.write(f"{seg['tekst']}\n\n")
    print(f"SRT zapisany: {wyjscie}")


if __name__ == "__main__":
    print("Whisper pipeline gotowy.")
    print("Użycie:")
    print("  wynik = transkrybuj('nagranie.mp3')")
    print("  print(wynik['tekst'])")
    print("  srt_eksport(wynik['segmenty'], 'napisy.srt')")
