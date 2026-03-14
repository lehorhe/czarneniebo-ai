# czarneniebo.whisper_transkrypcja

Transkrypcja audio/video z faster-whisper (GPU z fallbackiem na CPU).

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Funkcje

```python
def zaladuj_model(rozmiar: str = "medium", urzadzenie: str = "cuda") -> WhisperModel

def transkrybuj(
    sciezka_audio: str | pathlib.Path,
    jezyk: str = "pl",
    rozmiar: str = "medium",
    urzadzenie: str = "cuda",
    znaczniki_czasu: bool = True,
    filtr_ciszy: bool = True,
) -> dict

def transkrybuj_folder(
    folder: str | pathlib.Path,
    rozszerzenia: set = {".mp3", ".mp4", ".wav", ".ogg", ".m4a", ".flac"},
    jezyk: str = "pl",
) -> list[dict]

def srt_eksport(segmenty: list[dict], wyjscie: str | pathlib.Path) -> None
```

::: czarneniebo.whisper_transkrypcja
