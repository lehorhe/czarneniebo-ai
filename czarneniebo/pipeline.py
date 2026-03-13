"""
AI Pipeline dla Dziennikarstwa Śledczego
GPU: GTX 1660 SUPER 6.4GB | CPU: i5-12400F | RAM: 16GB
venv: C:/Users/rzecz/ai-pipeline/Scripts/activate

NER labels w pl_core_news_lg (NKJP):
  persName, orgName, placeName, geogName, date, time
"""

import os
import pathlib
import json
import hashlib
from datetime import datetime

import pdfplumber
import easyocr
import spacy
import chromadb
from sentence_transformers import SentenceTransformer
import ollama

# ── konfiguracja ──────────────────────────────────────────────
from czarneniebo.config import ARCHIWUM_DIR, DB_DIR, WYNIKI_DIR, MODELE_DIR, OLLAMA_MODEL_CHAT as OLLAMA_MODEL
# DB_DIR from config
# WYNIKI_DIR from config
# OLLAMA_MODEL from config

# ── ładowanie modeli ──────────────────────────────────────────
print("Ładowanie spaCy pl_core_news_lg...")
nlp = spacy.load("pl_core_news_lg")

print("Ładowanie sentence-transformers (multilingualny)...")
encoder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2", device="cpu")

print("Inicjalizacja ChromaDB...")
chroma = chromadb.PersistentClient(path=str(DB_DIR))
kolekcja = chroma.get_or_create_collection("archiwum_dziennikarskie")

print("Ładowanie EasyOCR (pl+en)...")
ocr = easyocr.Reader(["pl", "en"], gpu=True)


def doc_id(sciezka: pathlib.Path) -> str:
    """Unikalny ID dokumentu na podstawie ścieżki."""
    return hashlib.md5(str(sciezka).encode()).hexdigest()[:12]


def ekstrakcja_tekstu(sciezka: pathlib.Path) -> str:
    """Wyciąga tekst z PDF, obrazu lub pliku tekstowego."""
    ext = sciezka.suffix.lower()

    if ext == ".pdf":
        with pdfplumber.open(sciezka) as pdf:
            tekst = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        if len(tekst.strip()) < 100:
            # PDF skanowany — użyj OCR
            tekst = ekstrakcja_ocr(sciezka)
        return tekst

    elif ext in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}:
        return ekstrakcja_ocr(sciezka)

    elif ext in {".txt", ".md"}:
        return sciezka.read_text(encoding="utf-8", errors="ignore")

    return ""


def ekstrakcja_ocr(sciezka: pathlib.Path) -> str:
    """OCR przez EasyOCR."""
    wyniki = ocr.readtext(str(sciezka), detail=0, paragraph=True)
    return "\n".join(wyniki)


def ner_ekstrakcja(tekst: str) -> dict:
    """
    Wyciąga encje nazwane ze spaCy pl_core_news_lg.
    Labels NKJP: persName, orgName, placeName, geogName, date, time
    """
    doc = nlp(tekst[:100_000])  # spaCy limit
    return {
        "osoby":       [e.text for e in doc.ents if e.label_ == "persName"],
        "organizacje": [e.text for e in doc.ents if e.label_ == "orgName"],
        "miejsca":     [e.text for e in doc.ents if e.label_ in {"placeName", "geogName"}],
        "daty":        [e.text for e in doc.ents if e.label_ == "date"],
    }


def indeksuj_dokument(sciezka: pathlib.Path) -> dict:
    """Pełny pipeline: plik → tekst → NER → embedding → ChromaDB."""
    print(f"  Indeksuję: {sciezka.name}")
    did = doc_id(sciezka)

    tekst = ekstrakcja_tekstu(sciezka)
    if not tekst.strip():
        print(f"  [POMIŃ] Brak tekstu: {sciezka.name}")
        return {}

    encje = ner_ekstrakcja(tekst)
    embedding = encoder.encode(tekst[:8192]).tolist()

    meta = {
        "plik": sciezka.name,
        "sciezka": str(sciezka),
        "data_indeksowania": datetime.now().isoformat(),
        "osoby": json.dumps(list(set(encje["osoby"][:20])), ensure_ascii=False),
        "organizacje": json.dumps(list(set(encje["organizacje"][:20])), ensure_ascii=False),
        "miejsca": json.dumps(list(set(encje["miejsca"][:20])), ensure_ascii=False),
    }

    kolekcja.upsert(
        documents=[tekst[:10_000]],
        embeddings=[embedding],
        ids=[did],
        metadatas=[meta],
    )

    wynik = {**encje, "id": did, "plik": sciezka.name, "dlugosc": len(tekst)}
    print(f"  OK — {len(tekst)} znaków, {len(encje['osoby'])} osób, {len(encje['organizacje'])} org")
    return wynik


def indeksuj_folder(folder: pathlib.Path = ARCHIWUM_DIR):
    """Indeksuje wszystkie obsługiwane pliki w folderze."""
    rozszerzenia = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".txt"}
    pliki = [p for p in folder.rglob("*") if p.suffix.lower() in rozszerzenia]
    print(f"\nZnaleziono {len(pliki)} plików do indeksowania...\n")
    for p in pliki:
        indeksuj_dokument(p)
    print(f"\nGotowe. Dokumenty w bazie: {kolekcja.count()}")


def szukaj(pytanie: str, n: int = 5) -> list[dict]:
    """Semantyczne przeszukiwanie archiwum."""
    emb = encoder.encode(pytanie).tolist()
    wyniki = kolekcja.query(
        query_embeddings=[emb],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {
            "plik": wyniki["metadatas"][0][i]["plik"],
            "fragment": wyniki["documents"][0][i][:500],
            "odleglosc": round(wyniki["distances"][0][i], 4),
            "osoby": json.loads(wyniki["metadatas"][0][i].get("osoby", "[]")),
            "organizacje": json.loads(wyniki["metadatas"][0][i].get("organizacje", "[]")),
        }
        for i in range(len(wyniki["ids"][0]))
    ]


def zapytaj_archiwum(pytanie: str, n_kontekst: int = 3) -> str:
    """RAG: ChromaDB → Bielik → odpowiedź z cytatami."""
    trafienia = szukaj(pytanie, n=n_kontekst)
    if not trafienia:
        return "Brak dokumentów w archiwum. Uruchom najpierw indeksuj_folder()."

    kontekst = "\n\n---\n\n".join(
        f"[{t['plik']}]\n{t['fragment']}" for t in trafienia
    )

    prompt = f"""Na podstawie poniższych dokumentów z archiwum dziennikarskiego odpowiedz na pytanie.
Podaj konkretne fakty i wskaż źródło (nazwę pliku).

DOKUMENTY:
{kontekst}

PYTANIE: {pytanie}

ODPOWIEDŹ:"""

    odpowiedz = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return odpowiedz["message"]["content"]


if __name__ == "__main__":
    print("Pipeline gotowy.")
    print(f"Dokumenty w bazie: {kolekcja.count()}")
    print("\nUżycie:")
    print("  indeksuj_folder()          # zaindeksuj archiwum")
    print("  szukaj('Jan Kowalski')     # znajdź dokumenty")
    print("  zapytaj_archiwum('...')    # RAG z Bielikiem")
