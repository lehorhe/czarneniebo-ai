#!/usr/bin/env python3
"""
Czarne Niebo AI — testy E2E na realnych materialach z D:\
==========================================================
Uruchamia kazdy modul pipeline'u na wybranych plikach,
mierzy czas i VRAM, zapisuje wyniki i raport zbiorczy.

Uzycie:
    python scripts/test_e2e.py                    # wszystkie testy
    python scripts/test_e2e.py --tylko T1a        # jeden test
    python scripts/test_e2e.py --tylko T1a T2a    # wybrane testy
    python scripts/test_e2e.py --lista            # pokaz dostepne testy
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))

# Katalog wynikow - uzywamy config.py
from czarneniebo.config import WYNIKI_DIR

WYNIKI_E2E = WYNIKI_DIR / "testy_e2e"
WYNIKI_E2E.mkdir(parents=True, exist_ok=True)

# ── definicje testow ─────────────────────────────────────────────────────────

TESTY = {
    # T1: Whisper transkrypcja
    "T1a": {
        "opis": "Whisper PL — krotki wywiad (Rey1.mp4, ~700MB)",
        "modul": "whisper",
        "plik": Path("D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Rey1.mp4"),
        "jezyk": "pl",
        "timeout_min": 60,
    },
    "T1b": {
        "opis": "Whisper UA — raport z Kijowa (36MB MP3)",
        "modul": "whisper",
        "plik": Path("D:/RETRO/multi/audio/raport_z_kijowa.mp3"),
        "jezyk": "uk",
        "timeout_min": 15,
    },
    "T1c": {
        "opis": "Whisper PL — stress test (Felsztinski, 3.4GB)",
        "modul": "whisper",
        "plik": Path("D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Felsztinski_PL_FINAL.mp4"),
        "jezyk": "pl",
        "timeout_min": 180,
    },
    # T2: RAG — indeksowanie dokumentow
    "T2a": {
        "opis": "RAG — maly PDF (Black Sky AI, 87KB)",
        "modul": "rag",
        "plik": Path("D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/Black Sky AI in disinformation scenario.pdf"),
        "zapytanie": "Jak AI pomaga w walce z dezinformacja?",
        "timeout_min": 5,
    },
    "T2b": {
        "opis": "RAG — instrukcja redakcji AI (286KB PDF)",
        "modul": "rag",
        "plik": Path("D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/Instrukcja i Podr\u0119cznik Redakcji AI.pdf"),
        "zapytanie": "Jakie sa zasady weryfikacji informacji?",
        "timeout_min": 5,
    },
    "T2c": {
        "opis": "RAG — raport EEAS (11MB PDF, duzy)",
        "modul": "rag",
        "plik": Path("D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/EEAS-3nd-ThreatReport-March-2025-05-Digital-HD.pdf"),
        "zapytanie": "Jakie sa glowne zagrozenia dezinformacyjne w 2025?",
        "timeout_min": 10,
    },
    # T3: Forensics — detekcja deepfake
    "T3a": {
        "opis": "Forensics — autentyczny scan (strona1.jpg, baseline)",
        "modul": "forensics",
        "plik": Path("D:/ZDJECIA_GRAFIKA/Zdjecia_Downloads/Grodzisk/ogloszenie/strona1.jpg"),
        "oczekiwany_wynik": "PRAWDOPODOBNIE_AUTENTYCZNY",
        "timeout_min": 5,
    },
    "T3b": {
        "opis": "Forensics wideo — material produkcyjny LM 2025 (pierwsze 30s)",
        "modul": "forensics_video",
        "plik": Path("D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Fotyga.mp4"),
        "timeout_min": 10,
    },
    # T4: NER z transkrypcji (wymaga najpierw T1b)
    "T4a": {
        "opis": "NER + Graf — z krotkim textem testowym",
        "modul": "ner",
        "tekst": "Prezydent Ukrainy Wołodymyr Zełenski spotkał się z premierem Polski Donaldem Tuskiem w Warszawie 14 marca 2026 roku. Omawiali wsparcie dla Ukrainy.",
        "timeout_min": 2,
    },
}

# ── pomiar VRAM ──────────────────────────────────────────────────────────────

def vram_mb() -> int:
    """Zwraca uzycie VRAM w MB lub -1 jezeli nvidia-smi niedostepne."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            return int(r.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return -1


# ── wykonanie testow ─────────────────────────────────────────────────────────

def uruchom_whisper(cfg: dict) -> dict:
    from czarneniebo.whisper_transkrypcja import transkrybuj
    plik = cfg["plik"]
    jezyk = cfg.get("jezyk", "pl")

    wynik = transkrybuj(plik, jezyk=jezyk, rozmiar="medium", urzadzenie="cuda")

    # Zapisz wynik JSON
    out = WYNIKI_E2E / f"{cfg['_id']}_transkrypcja.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "plik": str(plik),
            "jezyk_wejscie": jezyk,
            "jezyk_wykryty": wynik.get("jezyk", "?"),
            "dlugosc_s": wynik.get("dlugosc_s", 0),
            "tekst_fragment": wynik.get("tekst", "")[:500] + "...",
            "segmentow": len(wynik.get("segmenty", [])),
        }, f, ensure_ascii=False, indent=2)

    return {
        "status": "OK",
        "jezyk_wykryty": wynik.get("jezyk", "?"),
        "dlugosc_s": round(wynik.get("dlugosc_s", 0), 1),
        "segmentow": len(wynik.get("segmenty", [])),
        "wynik_plik": str(out),
        "tekst_fragment": wynik.get("tekst", "")[:200],
    }


def uruchom_rag(cfg: dict) -> dict:
    from czarneniebo.pipeline import indeksuj_dokument, zapytaj_archiwum
    plik = cfg["plik"]
    zapytanie = cfg.get("zapytanie", "Co zawiera ten dokument?")

    meta = indeksuj_dokument(plik)
    odpowiedz = zapytaj_archiwum(zapytanie, n_kontekst=3)

    out = WYNIKI_E2E / f"{cfg['_id']}_rag.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "plik": str(plik),
            "indeksowanie": meta,
            "zapytanie": zapytanie,
            "odpowiedz_fragment": odpowiedz[:500],
        }, f, ensure_ascii=False, indent=2)

    return {
        "status": "OK",
        "fragmentow_zindeksowanych": meta.get("fragmentow", "?"),
        "odpowiedz_fragment": odpowiedz[:200],
        "wynik_plik": str(out),
    }


def uruchom_forensics(cfg: dict) -> dict:
    from czarneniebo.forensics_pipeline import ForensicsAnalyzer
    plik = cfg["plik"]
    oczekiwany = cfg.get("oczekiwany_wynik", None)

    analyzer = ForensicsAnalyzer()
    raport = analyzer.analizuj(plik)
    sciezka_raportu = analyzer.zapisz_raport(raport, WYNIKI_E2E)

    zgodnosc = None
    if oczekiwany:
        zgodnosc = raport.etykieta == oczekiwany

    return {
        "status": "OK",
        "etykieta": raport.etykieta,
        "poziom_pewnosci": round(raport.poziom_pewnosci, 3),
        "sygnaly": {k: round(v.get("wynik", 0), 3) for k, v in raport.sygnaly.items()},
        "oczekiwany": oczekiwany,
        "zgodnosc_z_oczekiwanym": zgodnosc,
        "wynik_plik": str(sciezka_raportu),
    }


def uruchom_ner(cfg: dict) -> dict:
    from czarneniebo.pipeline import ner_ekstrakcja
    tekst = cfg.get("tekst", "")

    encje = ner_ekstrakcja(tekst)

    out = WYNIKI_E2E / f"{cfg['_id']}_ner.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"tekst": tekst, "encje": encje}, f, ensure_ascii=False, indent=2)

    return {
        "status": "OK",
        "encje_lacznie": sum(len(v) for v in encje.values()),
        "typy": {k: len(v) for k, v in encje.items() if v},
        "wynik_plik": str(out),
    }


WYKONAWCY = {
    "whisper": uruchom_whisper,
    "rag": uruchom_rag,
    "forensics": uruchom_forensics,
    "forensics_video": uruchom_forensics,  # ten sam analyzer, inne wejscie
    "ner": uruchom_ner,
}


# ── glowna petla ─────────────────────────────────────────────────────────────

def uruchom_test(test_id: str) -> dict:
    cfg = dict(TESTY[test_id])
    cfg["_id"] = test_id

    plik = cfg.get("plik")
    if plik and not Path(plik).exists():
        return {
            "id": test_id,
            "opis": cfg["opis"],
            "status": "POMINIETY",
            "powod": f"Plik nie istnieje: {plik}",
            "czas_s": 0,
            "vram_przed": -1,
            "vram_po": -1,
            "vram_delta": 0,
        }

    modul = cfg["modul"]
    wykonawca = WYKONAWCY.get(modul)
    if not wykonawca:
        return {
            "id": test_id,
            "opis": cfg["opis"],
            "status": "BLAD",
            "powod": f"Nieznany modul: {modul}",
            "czas_s": 0,
        }

    print(f"\n[{test_id}] {cfg['opis']}")
    if plik:
        rozmiar_mb = Path(plik).stat().st_size / 1024 / 1024
        print(f"  Plik: {Path(plik).name} ({rozmiar_mb:.0f} MB)")

    vram_przed = vram_mb()
    t_start = time.time()

    try:
        wynik = wykonawca(cfg)
        czas_s = round(time.time() - t_start, 1)
        vram_po = vram_mb()
        delta = (vram_po - vram_przed) if vram_przed >= 0 and vram_po >= 0 else 0

        print(f"  [OK] {czas_s}s | VRAM: {vram_przed}→{vram_po} MB (delta: +{delta} MB)")
        if "etykieta" in wynik:
            print(f"  Wynik: {wynik['etykieta']} ({wynik.get('poziom_pewnosci', '?')})")
        elif "tekst_fragment" in wynik:
            print(f"  Fragment: {wynik['tekst_fragment'][:100]}...")

        return {
            "id": test_id,
            "opis": cfg["opis"],
            "status": wynik.get("status", "OK"),
            "czas_s": czas_s,
            "vram_przed_mb": vram_przed,
            "vram_po_mb": vram_po,
            "vram_delta_mb": delta,
            **{k: v for k, v in wynik.items() if k != "status"},
        }

    except Exception as e:
        czas_s = round(time.time() - t_start, 1)
        print(f"  [BLAD] {czas_s}s — {e}")
        return {
            "id": test_id,
            "opis": cfg["opis"],
            "status": "BLAD",
            "powod": str(e),
            "czas_s": czas_s,
            "vram_przed_mb": vram_przed,
            "vram_po_mb": vram_mb(),
        }


def generuj_raport(wyniki: list[dict], ts: str):
    raport_json = WYNIKI_E2E / f"RAPORT_{ts}.json"
    with open(raport_json, "w", encoding="utf-8") as f:
        json.dump(wyniki, f, ensure_ascii=False, indent=2)

    raport_md = WYNIKI_E2E / f"RAPORT_{ts}.md"
    ok = sum(1 for w in wyniki if w["status"] == "OK")
    blad = sum(1 for w in wyniki if w["status"] == "BLAD")
    pominiety = sum(1 for w in wyniki if w["status"] == "POMINIETY")

    linie = [
        f"# Raport testow E2E — Czarne Niebo AI",
        f"**Data:** {ts.replace('_', ' ')}",
        f"**Wyniki:** {ok} OK | {blad} BLAD | {pominiety} POMINIETY",
        "",
        "## Tabela wynikow",
        "",
        "| Test | Opis | Status | Czas (s) | VRAM delta (MB) | Uwagi |",
        "|------|------|--------|----------|-----------------|-------|",
    ]

    for w in wyniki:
        uwagi = ""
        if w["status"] == "BLAD":
            uwagi = w.get("powod", "")[:60]
        elif w["status"] == "POMINIETY":
            uwagi = w.get("powod", "")[:60]
        elif "etykieta" in w:
            zgodnosc = w.get("zgodnosc_z_oczekiwanym")
            znak = " [OK]" if zgodnosc else (" [NIEZG]" if zgodnosc is False else "")
            uwagi = f"{w['etykieta']} ({w.get('poziom_pewnosci', '?')}){znak}"
        elif "dlugosc_s" in w:
            uwagi = f"{w['dlugosc_s']}s audio, {w.get('segmentow', '?')} segm, jezyk: {w.get('jezyk_wykryty', '?')}"
        elif "encje_lacznie" in w:
            uwagi = f"{w['encje_lacznie']} encji: {w.get('typy', {})}"

        linie.append(
            f"| {w['id']} | {w['opis'][:40]} | {w['status']} "
            f"| {w.get('czas_s', '-')} | {w.get('vram_delta_mb', '-')} | {uwagi} |"
        )

    linie += ["", "---", f"*Wygenerowano automatycznie przez scripts/test_e2e.py*"]

    with open(raport_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linie))

    return raport_md


def main():
    parser = argparse.ArgumentParser(description="Czarne Niebo AI — testy E2E")
    parser.add_argument("--tylko", nargs="+", metavar="ID",
                        help="Uruchom tylko wybrane testy (np. T1a T2a)")
    parser.add_argument("--lista", action="store_true",
                        help="Wyswietl dostepne testy i wyjdz")
    args = parser.parse_args()

    if args.lista:
        print("\nDostepne testy:\n")
        for tid, cfg in TESTY.items():
            plik = cfg.get("plik", "-")
            istnieje = "[OK]" if Path(plik).exists() else "[BRAK]" if plik != "-" else ""
            print(f"  {tid:6s}  {cfg['opis'][:55]:55s}  {istnieje}")
        return

    wybrane = args.tylko if args.tylko else list(TESTY.keys())
    nieznane = [t for t in wybrane if t not in TESTY]
    if nieznane:
        print(f"[BLAD] Nieznane ID testow: {nieznane}")
        print(f"Dostepne: {list(TESTY.keys())}")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\nCzarne Niebo AI — testy E2E [{ts}]")
    print(f"Uruchamiam {len(wybrane)} test(ow): {wybrane}")
    print(f"Wyniki: {WYNIKI_E2E}")

    wyniki = []
    for tid in wybrane:
        wynik = uruchom_test(tid)
        wyniki.append(wynik)

    raport = generuj_raport(wyniki, ts)
    print(f"\n{'='*60}")
    ok = sum(1 for w in wyniki if w["status"] == "OK")
    print(f"Zakonczone: {ok}/{len(wyniki)} OK")
    print(f"Raport: {raport}")


if __name__ == "__main__":
    main()
