"""
File Watcher — automatyczne indeksowanie archiwum
Monitoruje folder i indeksuje nowe pliki gdy tylko się pojawią.

Uruchomienie (osobne okno terminala):
  C:/Users/rzecz/ai-pipeline/Scripts/python.exe file_watcher.py
"""

import time
import pathlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from czarneniebo.config import ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR, OLLAMA_MODEL_CHAT as OLLAMA_MODEL
OBSŁUGIWANE = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".txt", ".mp3", ".mp4", ".wav"}


class ArchiwumHandler(FileSystemEventHandler):
    def __init__(self):
        # Lazy import żeby watcher startował szybko
        self._pipeline = None
        self._whisper = None

    def _zaladuj_pipeline(self):
        if self._pipeline is None:
            print("Ładowanie pipeline...")
            from czarneniebo import pipeline
            self._pipeline = pipeline
        return self._pipeline

    def on_created(self, event):
        if event.is_directory:
            return
        sciezka = pathlib.Path(event.src_path)
        if sciezka.suffix.lower() not in OBSŁUGIWANE:
            return

        print(f"\n[NOWY PLIK] {sciezka.name}")

        # Poczekaj chwilę aż plik się zapisze (kopiowanie może trwać)
        time.sleep(1)

        try:
            if sciezka.suffix.lower() in {".mp3", ".mp4", ".wav", ".ogg", ".m4a", ".flac"}:
                self._obsłuż_audio(sciezka)
            else:
                p = self._zaladuj_pipeline()
                wynik = p.indeksuj_dokument(sciezka)
                if wynik:
                    print(f"[OK] Zaindeksowano: {sciezka.name}")
        except Exception as e:
            print(f"[BŁĄD] {sciezka.name}: {e}")

    def _obsłuż_audio(self, sciezka: pathlib.Path):
        """Transkrybuje audio, zapisuje TXT i indeksuje transkrypcję."""
        from czarneniebo.whisper_transkrypcja import transkrybuj
        print(f"Transkrybuję audio: {sciezka.name}")
        wynik = transkrybuj(sciezka, jezyk="pl")

        # Zapisz transkrypcję jako TXT
        txt_path = sciezka.with_suffix(".transkrypcja.txt")
        txt_path.write_text(wynik["tekst"], encoding="utf-8")
        print(f"Transkrypcja zapisana: {txt_path.name}")

        # Zaindeksuj transkrypcję w ChromaDB
        p = self._zaladuj_pipeline()
        p.indeksuj_dokument(txt_path)


def start(folder: pathlib.Path = ARCHIWUM_DIR):
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Monitoruję: {folder}")
    print("Wrzuć PDF, zdjęcie lub audio do folderu — zostanie zaindeksowane automatycznie.")
    print("Ctrl+C aby zatrzymać.\n")

    observer = Observer()
    observer.schedule(ArchiwumHandler(), path=str(folder), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nWatcher zatrzymany.")
    observer.join()


if __name__ == "__main__":
    start()
