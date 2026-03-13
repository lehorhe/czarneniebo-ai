"""
Restauracja mediów archiwalnych
- Demucs: separacja głosu od tła/szumu w nagraniach
- Real-ESRGAN: upscaling i restauracja zdjęć/skanów (wymaga osobnej instalacji)
- GFPGAN: restauracja twarzy (wymaga osobnej instalacji)

Demucs działa natychmiast po pip install demucs.
Real-ESRGAN: pip install realesrgan basicsr (może wymagać Visual C++ Build Tools)

Użycie Demucs:
  python restauracja_mediow.py audio nagranie.mp3

  Wynik w folderze: separated/htdemucs/<nazwa_pliku>/
    vocals.wav    — wyizolowany głos
    no_vocals.wav — muzyka/tło bez głosu
"""

import pathlib
import subprocess
import sys
from czarneniebo.config import WYNIKI_DIR as _WYNIKI_DIR


def demucs_separuj(
    sciezka_audio: str | pathlib.Path,
    folder_wyjsciowy: str | pathlib.Path = str(_WYNIKI_DIR / "separated"),
    model: str = "htdemucs",
    tylko_glos: bool = True,
) -> dict:
    """
    Separuje głos od tła dźwiękowego.

    Args:
        sciezka_audio: Plik audio/video (mp3, mp4, wav, ogg, ...)
        folder_wyjsciowy: Gdzie zapisać wyniki
        model: Model Demucs ("htdemucs" = domyślny, dobry do mowy)
        tylko_glos: True = separuj vocal/no_vocal; False = 4 ścieżki

    Returns:
        dict z ścieżkami do wynikowych plików
    """
    sciezka = pathlib.Path(sciezka_audio)
    folder_wyj = pathlib.Path(folder_wyjsciowy)
    folder_wyj.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "demucs",
        "--out", str(folder_wyj),
        "--name", model,
    ]
    if tylko_glos:
        cmd += ["--two-stems", "vocals"]

    cmd.append(str(sciezka))

    print(f"Separuję: {sciezka.name}")
    print(f"Model: {model}, folder: {folder_wyj}")
    subprocess.run(cmd, check=True)

    wynik_dir = folder_wyj / model / sciezka.stem
    return {
        "glos": str(wynik_dir / "vocals.wav") if tylko_glos else None,
        "tlo": str(wynik_dir / "no_vocals.wav") if tylko_glos else None,
        "folder": str(wynik_dir),
    }


def real_esrgan_upscale(
    sciezka_obrazu: str | pathlib.Path,
    skala: int = 4,
    folder_wyjsciowy: str | pathlib.Path = str(_WYNIKI_DIR),
) -> str:
    """
    Upscaling obrazu przez Real-ESRGAN.
    Wymaga: pip install realesrgan basicsr

    Args:
        sciezka_obrazu: Plik JPG, PNG, TIFF
        skala: Współczynnik powiększenia (2 lub 4)
        folder_wyjsciowy: Folder wynikowy

    Returns:
        Ścieżka do przetworzonego obrazu
    """
    try:
        import cv2
        import numpy as np
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except ImportError:
        raise ImportError(
            "Zainstaluj: pip install realesrgan basicsr\n"
            "Może wymagać Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
        )

    from torchvision.transforms.functional import to_tensor
    import torch

    # Wybór modelu w zależności od skali
    if skala == 4:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        model_name = "RealESRGAN_x4plus"
    else:
        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
        model_name = "RealESRGAN_x2plus"

    upsampler = RealESRGANer(
        scale=skala,
        model_path=model_url,
        model=model,
        tile=400,           # ważne dla 6GB VRAM — przetwarza kafelkami
        tile_pad=10,
        pre_pad=0,
        half=True,          # fp16 = 2x mniej VRAM
        gpu_id=0,
    )

    sciezka = pathlib.Path(sciezka_obrazu)
    img = cv2.imread(str(sciezka), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Nie mogę otworzyć: {sciezka}")

    print(f"Upscaling {skala}x: {sciezka.name} ({img.shape[1]}x{img.shape[0]})")
    output, _ = upsampler.enhance(img, outscale=skala)

    folder_wyj = pathlib.Path(folder_wyjsciowy)
    folder_wyj.mkdir(parents=True, exist_ok=True)
    wyjscie = folder_wyj / f"{sciezka.stem}_x{skala}{sciezka.suffix}"
    cv2.imwrite(str(wyjscie), output)
    print(f"Zapisano: {wyjscie} ({output.shape[1]}x{output.shape[0]})")
    return str(wyjscie)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Użycie:")
        print("  python restauracja_mediow.py audio <plik.mp3>   — separacja głosu")
        print("  python restauracja_mediow.py obraz <plik.jpg>   — upscaling 4x")
        sys.exit(0)

    tryb = sys.argv[1].lower()
    plik = sys.argv[2]

    if tryb == "audio":
        wynik = demucs_separuj(plik)
        print(f"\nGłos: {wynik['glos']}")
        print(f"Tło: {wynik['tlo']}")
    elif tryb == "obraz":
        wynik = real_esrgan_upscale(plik)
        print(f"\nWynik: {wynik}")
    else:
        print(f"Nieznany tryb: {tryb}. Użyj 'audio' lub 'obraz'.")
