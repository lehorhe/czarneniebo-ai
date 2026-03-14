#!/usr/bin/env python3
"""
Czarne Niebo AI — testy E2E na realnych materialach z D:\
==========================================================
Kazdy test uruchamia sie w osobnym procesie Python (izolacja RAM).
Wyniki zapisywane jako JSON + raport zbiorczy RAPORT_*.md.

Uzycie:
    python scripts/test_e2e.py --lista           # pokaz dostepne testy
    python scripts/test_e2e.py --tylko T3a       # jeden test
    python scripts/test_e2e.py --tylko T3a T4a T2a
    python scripts/test_e2e.py                   # wszystkie
"""

import argparse
import json
import os
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

from czarneniebo.config import WYNIKI_DIR

WYNIKI_E2E = WYNIKI_DIR / "testy_e2e"
WYNIKI_E2E.mkdir(parents=True, exist_ok=True)

# ── definicje testow ─────────────────────────────────────────────────────────

TESTY = {
    "T1a": {
        "opis": "Whisper PL — krotki wywiad (Rey1.mp4, ~700MB)",
        "modul": "whisper",
        "plik": "D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Rey1.mp4",
        "jezyk": "pl",
        "timeout_min": 60,
    },
    "T1b": {
        "opis": "Whisper UA — raport z Kijowa (36MB MP3)",
        "modul": "whisper",
        "plik": "D:/RETRO/multi/audio/raport_z_kijowa.mp3",
        "jezyk": "uk",
        "timeout_min": 15,
    },
    "T1c": {
        "opis": "Whisper PL — stress test (Felsztinski, 3.4GB)",
        "modul": "whisper",
        "plik": "D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Felsztinski_PL_FINAL.mp4",
        "jezyk": "pl",
        "timeout_min": 180,
    },
    "T2a": {
        "opis": "RAG — maly PDF (Black Sky AI, 87KB)",
        "modul": "rag",
        "plik": "D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/Black Sky AI in disinformation scenario.pdf",
        "zapytanie": "Jak AI pomaga w walce z dezinformacja?",
        "timeout_min": 10,
    },
    "T2b": {
        "opis": "RAG — instrukcja redakcji AI (286KB PDF)",
        "modul": "rag",
        "plik": "D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/Instrukcja i Podr\u0119cznik Redakcji AI.pdf",
        "zapytanie": "Jakie sa zasady weryfikacji informacji?",
        "timeout_min": 10,
    },
    "T2c": {
        "opis": "RAG — raport EEAS (11MB PDF, duzy)",
        "modul": "rag",
        "plik": "D:/DOKUMENTY/Dokumenty_Downloads/Czarne_Niebo_docs/EEAS-3nd-ThreatReport-March-2025-05-Digital-HD.pdf",
        "zapytanie": "Jakie sa glowne zagrozenia dezinformacyjne w 2025?",
        "timeout_min": 15,
    },
    "T3a": {
        "opis": "Forensics — autentyczny scan (strona1.jpg, baseline)",
        "modul": "forensics",
        "plik": "D:/ZDJECIA_GRAFIKA/Zdjecia_Downloads/Grodzisk/ogloszenie/strona1.jpg",
        "oczekiwany_wynik": "PRAWDOPODOBNIE_AUTENTYCZNY",
        "timeout_min": 8,
    },
    "T3b": {
        "opis": "Forensics wideo — material produkcyjny (Fotyga.mp4)",
        "modul": "forensics",
        "plik": "D:/PRODUKCJA/CZARNE_NIEBO/NEWS/Finals/Fotyga.mp4",
        "timeout_min": 15,
    },
    "T4a": {
        "opis": "NER — tekst testowy PL (spaCy, bez sentence-transformers)",
        "modul": "ner",
        "tekst": "Prezydent Ukrainy Wolodymyr Zelenski spotkal sie z premierem Polski Donaldem Tuskiem w Warszawie 14 marca 2026 roku. Omawiali wsparcie dla Ukrainy i sankcje wobec Rosji.",
        "timeout_min": 3,
    },
}

# ── pomiar VRAM ──────────────────────────────────────────────────────────────

def vram_mb() -> int:
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


# ── worker (uruchamiany w subprocess) ────────────────────────────────────────

WORKER_SCRIPT = """
import sys, json, os
sys.path.insert(0, r'{repo_root}')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
# Lzejszy model embeddingow dla testow (470MB zamiast 1.1GB)
os.environ.setdefault('CN_EMBED_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')

cfg = {cfg_json}
modul = cfg['modul']
wynik_plik = r'{wynik_plik}'

try:
    if modul == 'whisper':
        from czarneniebo.whisper_transkrypcja import transkrybuj
        from pathlib import Path
        w = transkrybuj(cfg['plik'], jezyk=cfg.get('jezyk','pl'),
                        rozmiar='medium', urzadzenie='cuda')
        result = {{
            'status': 'OK',
            'jezyk_wykryty': w.get('jezyk','?'),
            'dlugosc_s': round(w.get('dlugosc_s',0), 1),
            'segmentow': len(w.get('segmenty',[])),
            'tekst_fragment': w.get('tekst','')[:300],
        }}
        # Pelny wynik
        import json as _j
        with open(wynik_plik.replace('.json','_full.json'), 'w', encoding='utf-8') as f:
            _j.dump({{'tekst': w.get('tekst',''), 'segmenty': w.get('segmenty',[])}}, f, ensure_ascii=False, indent=2)

    elif modul == 'rag':
        # PDF ekstrakcja + direct Q&A przez Bielik (bez modelu embeddingow)
        # Testuje workflow: tekst z dokumentu -> kontekst dla LLM -> odpowiedz
        import pdfplumber, ollama
        from pathlib import Path
        plik_path = Path(cfg['plik'])

        # 1) Ekstrakcja tekstu
        with pdfplumber.open(str(plik_path)) as pdf:
            tekst = '\\n'.join(p.extract_text() or '' for p in pdf.pages)
        tekst = tekst.strip()
        if not tekst:
            raise ValueError('Pusty tekst z PDF')

        # 2) Zapytanie do Bielika z kontekstem dokumentu
        zapytanie = cfg.get('zapytanie', 'Co zawiera ten dokument?')
        kontekst = tekst[:4000]
        resp = ollama.chat(
            model='SpeakLeash/bielik-7b-instruct-v0.1-gguf:Q4_K_S',
            messages=[{{'role':'user','content':'Kontekst: ' + kontekst + '\\n\\nPytanie: ' + zapytanie}}],
            options={{'num_predict':200, 'temperature':0.1}}
        )
        odpowiedz = resp['message']['content']

        result = {{
            'status': 'OK',
            'znakow_tekstu': len(tekst),
            'odpowiedz_fragment': odpowiedz[:400],
        }}

    elif modul == 'forensics':
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        from pathlib import Path
        analyzer = ForensicsAnalyzer()
        raport = analyzer.analizuj(Path(cfg['plik']))
        analyzer.zapisz_raport(raport, Path(r'{wyniki_e2e}'))
        oczekiwany = cfg.get('oczekiwany_wynik')
        result = {{
            'status': 'OK',
            'etykieta': raport.etykieta,
            'poziom_pewnosci': round(raport.poziom_pewnosci, 3),
            'sygnaly': {{k: round(float(v.wynik), 3) for k,v in raport.sygnaly.items()}},
            'zgodnosc_z_oczekiwanym': (raport.etykieta == oczekiwany) if oczekiwany else None,
        }}

    elif modul == 'ner':
        import spacy
        nlp = spacy.load('pl_core_news_lg')
        doc = nlp(cfg.get('tekst', ''))
        encje = {{}}
        for ent in doc.ents:
            encje.setdefault(ent.label_, []).append(ent.text)
        result = {{
            'status': 'OK',
            'encje_lacznie': sum(len(v) for v in encje.values()),
            'typy': {{k: v for k,v in encje.items()}},
        }}

    else:
        result = {{'status': 'BLAD', 'powod': f'Nieznany modul: {{modul}}'}}

except MemoryError as e:
    result = {{'status': 'OOM', 'powod': f'Out of memory: {{e}}'}}
except Exception as e:
    import traceback
    result = {{'status': 'BLAD', 'powod': str(e), 'traceback': traceback.format_exc()[-800:]}}

import json as _j
with open(wynik_plik, 'w', encoding='utf-8') as f:
    _j.dump(result, f, ensure_ascii=False, indent=2)
print('WYNIK_OK')
"""


def uruchom_test(test_id: str) -> dict:
    cfg = TESTY[test_id]
    plik = cfg.get("plik")

    if plik and not Path(plik).exists():
        return {
            "id": test_id, "opis": cfg["opis"], "status": "POMINIETY",
            "powod": f"Plik nie istnieje: {plik}", "czas_s": 0,
        }

    wynik_plik = str(WYNIKI_E2E / f"{test_id}_wynik.json")
    # Usun stary plik - bedziemy wiedziec ze wynik jest swiezy
    Path(wynik_plik).unlink(missing_ok=True)
    timeout_s = cfg.get("timeout_min", 10) * 60

    print(f"\n[{test_id}] {cfg['opis']}")
    if plik:
        mb = Path(plik).stat().st_size / 1024 / 1024
        print(f"  Plik: {Path(plik).name} ({mb:.0f} MB)")

    # Buduj skrypt workera
    script = WORKER_SCRIPT.format(
        repo_root=str(REPO_ROOT).replace("\\", "\\\\"),
        cfg_json=json.dumps(cfg, ensure_ascii=False),
        wynik_plik=wynik_plik.replace("\\", "\\\\"),
        wyniki_e2e=str(WYNIKI_E2E).replace("\\", "\\\\"),
    )

    vram_przed = vram_mb()
    t_start = time.time()
    env = {**os.environ, "TOKENIZERS_PARALLELISM": "false", "PYTHONIOENCODING": "utf-8"}

    try:
        r = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True,
            timeout=timeout_s, env=env, encoding="utf-8", errors="replace"
        )
        czas_s = round(time.time() - t_start, 1)
        vram_po = vram_mb()
        delta = (vram_po - vram_przed) if vram_przed >= 0 and vram_po >= 0 else 0

        # Wczytaj wynik z pliku JSON
        wynik_path = Path(wynik_plik)
        if wynik_path.exists():
            with open(wynik_path, encoding="utf-8") as f:
                wynik = json.load(f)
        else:
            stderr_tail = r.stderr[-600:] if r.stderr else ""
            stdout_tail = r.stdout[-300:] if r.stdout else ""
            wynik = {"status": "BLAD", "powod": f"Brak pliku wynikowego. stderr: {stderr_tail} stdout: {stdout_tail}"}

        status = wynik.get("status", "BLAD")
        print(f"  [{status}] {czas_s}s | VRAM: {vram_przed}→{vram_po} MB (delta: +{delta})")

        if status == "OK":
            if "etykieta" in wynik:
                print(f"  Wynik: {wynik['etykieta']} (pewnosc: {wynik.get('poziom_pewnosci','?')})")
            elif "tekst_fragment" in wynik:
                print(f"  Fragment: {str(wynik['tekst_fragment'])[:120]}...")
            elif "encje_lacznie" in wynik:
                print(f"  Encje: {wynik['encje_lacznie']} — {wynik.get('typy',{})}")
            elif "odpowiedz_fragment" in wynik:
                print(f"  Odpowiedz: {str(wynik['odpowiedz_fragment'])[:120]}...")
        elif status in ("BLAD", "OOM"):
            print(f"  Powod: {wynik.get('powod','?')[:200]}")

        return {
            "id": test_id, "opis": cfg["opis"],
            "czas_s": czas_s,
            "vram_przed_mb": vram_przed, "vram_po_mb": vram_po, "vram_delta_mb": delta,
            **wynik,
        }

    except subprocess.TimeoutExpired:
        czas_s = round(time.time() - t_start, 1)
        print(f"  [TIMEOUT] {czas_s}s (limit: {timeout_s}s)")
        return {
            "id": test_id, "opis": cfg["opis"], "status": "TIMEOUT",
            "powod": f"Przekroczono {cfg.get('timeout_min',10)} min",
            "czas_s": czas_s,
        }
    except Exception as e:
        return {
            "id": test_id, "opis": cfg["opis"], "status": "BLAD",
            "powod": str(e), "czas_s": round(time.time() - t_start, 1),
        }


# ── raport ────────────────────────────────────────────────────────────────────

def generuj_raport(wyniki: list, ts: str) -> Path:
    raport_json = WYNIKI_E2E / f"RAPORT_{ts}.json"
    with open(raport_json, "w", encoding="utf-8") as f:
        json.dump(wyniki, f, ensure_ascii=False, indent=2)

    ok = sum(1 for w in wyniki if w.get("status") == "OK")
    blad = sum(1 for w in wyniki if w.get("status") in ("BLAD", "OOM", "TIMEOUT"))
    pomin = sum(1 for w in wyniki if w.get("status") == "POMINIETY")

    linie = [
        "# Raport testow E2E — Czarne Niebo AI",
        f"**Data:** {ts.replace('_', ' ')}",
        f"**Wyniki:** {ok} OK / {blad} BLAD / {pomin} POMINIETY",
        "",
        "| Test | Opis | Status | Czas (s) | VRAM delta | Uwagi |",
        "|------|------|--------|----------|------------|-------|",
    ]
    for w in wyniki:
        uwagi = ""
        s = w.get("status", "?")
        if s in ("BLAD", "OOM", "TIMEOUT"):
            uwagi = str(w.get("powod", ""))[:60]
        elif "etykieta" in w:
            zgodnosc = w.get("zgodnosc_z_oczekiwanym")
            ok_str = " [OK]" if zgodnosc else (" [NIEZG]" if zgodnosc is False else "")
            uwagi = f"{w['etykieta']} ({w.get('poziom_pewnosci','?')}){ok_str}"
        elif "dlugosc_s" in w:
            uwagi = f"{w['dlugosc_s']}s audio, {w.get('segmentow','?')} segm, jezyk: {w.get('jezyk_wykryty','?')}"
        elif "encje_lacznie" in w:
            uwagi = f"{w['encje_lacznie']} encji"
        elif "odpowiedz_fragment" in w:
            uwagi = str(w["odpowiedz_fragment"])[:50]

        linie.append(
            f"| {w['id']} | {w['opis'][:38]} | **{s}** "
            f"| {w.get('czas_s','-')} | {w.get('vram_delta_mb','-')} | {uwagi} |"
        )

    linie += ["", "---", "*Wygenerowano przez scripts/test_e2e.py*"]
    raport_md = WYNIKI_E2E / f"RAPORT_{ts}.md"
    with open(raport_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linie))
    return raport_md


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Czarne Niebo AI — testy E2E")
    parser.add_argument("--tylko", nargs="+", metavar="ID")
    parser.add_argument("--lista", action="store_true")
    args = parser.parse_args()

    if args.lista:
        print("\nDostepne testy:\n")
        for tid, cfg in TESTY.items():
            p = cfg.get("plik", "-")
            istnieje = "[OK]  " if (p == "-" or Path(p).exists()) else "[BRAK]"
            print(f"  {tid:5s} {istnieje}  {cfg['opis']}")
        return

    wybrane = args.tylko or list(TESTY.keys())
    nieznane = [t for t in wybrane if t not in TESTY]
    if nieznane:
        print(f"Nieznane ID: {nieznane}. Dostepne: {list(TESTY.keys())}")
        sys.exit(1)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\nCzarne Niebo AI — testy E2E [{ts}]")
    print(f"Uruchamiam {len(wybrane)} test(ow): {wybrane}")
    print(f"Izolacja RAM: kazdy test w osobnym procesie Python")
    print(f"Wyniki: {WYNIKI_E2E}")

    wyniki = [uruchom_test(tid) for tid in wybrane]
    raport = generuj_raport(wyniki, ts)

    ok = sum(1 for w in wyniki if w.get("status") == "OK")
    print(f"\n{'='*55}")
    print(f"Zakonczone: {ok}/{len(wyniki)} OK  |  Raport: {raport.name}")


if __name__ == "__main__":
    main()
