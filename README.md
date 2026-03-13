# Archiwum Dziennikarskie AI

**GTX 1660 SUPER 6.4GB · i5-12400F · 16GB RAM · Windows 11**

## Szybki start

```bat
# Aktywuj środowisko
C:\Users\rzecz\ai-pipeline\Scripts\activate.bat

# Lub kliknij dwukrotnie:
URUCHOM.bat
```

## Struktura projektu

```
AI-Dziennikarstwo/
├── URUCHOM.bat              ← punkt wejścia
├── pipeline.py              ← rdzeń: OCR + NER + ChromaDB + RAG z Bielikiem
├── whisper_transkrypcja.py  ← audio/video → tekst (Whisper medium PL)
├── restauracja_mediow.py    ← Demucs (separacja głosu) + Real-ESRGAN (upscaling)
├── graf_powiazań.py         ← NetworkX + PyVis graf OSINT
├── dezinformacja.py         ← Logistic Regression + sentence-transformers
├── web_ui.py                ← Gradio UI http://localhost:7860
├── file_watcher.py          ← auto-indeksowanie folderu archiwum
├── archiwum/                ← TU wrzucaj dokumenty
├── wyniki/                  ← wyniki pipeline, grafy HTML
├── archiwum_db/             ← ChromaDB (baza wektorowa)
└── modele/                  ← zapisane modele sklearn
```

## Komponenty i ich przeznaczenie

| Komponent | Zadanie | GPU/CPU |
|-----------|---------|---------|
| Ollama + Bielik | Odpowiedzi po polsku (RAG) | GPU 4.1GB |
| Ollama + Moondream | Opisy i analiza zdjęć | GPU 1.7GB |
| faster-whisper medium | Transkrypcja PL (archiwalne nagrania) | GPU ~3GB |
| Real-ESRGAN | Upscaling skanów i zdjęć 4x | GPU (kafelki) |
| Demucs | Separacja głosu z szumu | CPU/GPU |
| spaCy pl_core_news_lg | NER: persName, orgName, placeName, date | CPU |
| ChromaDB | Semantyczna baza wiedzy | CPU |
| sentence-transformers | Embeddingi multilingwalne | CPU/GPU |
| NetworkX + PyVis | Graf powiązań OSINT | CPU |
| Logistic Regression | Detekcja dezinformacji (0.002s/art.) | CPU |
| Gradio Web UI | Interfejs dla dziennikarzy | - |
| watchdog | Auto-indeksowanie folderu | CPU |

## Przepływ danych

```
[Folder archiwum]
       ↓ (watchdog — automatycznie)
  ┌────────────────────────────────────┐
  │  PDF        → pdfplumber/EasyOCR   │
  │  Obraz      → EasyOCR              │
  │  Audio/Video → faster-whisper      │
  └─────────────┬──────────────────────┘
                ↓
        spaCy NER → osoby, org, miejsca
                ↓
    sentence-transformers → embedding
                ↓
           ChromaDB
                ↓
   [Gradio UI] ← dziennikarz pyta po polsku
                ↓
     ChromaDB → top-5 trafień (kontekst)
                ↓
         Ollama/Bielik → odpowiedź
                ↓
    NetworkX graf powiązań (z NER)
```

## Ograniczenia sprzętowe

- **6GB VRAM:** Jeden duży model naraz. Bielik (4.1GB) + Whisper medium (~2GB) = za dużo jednocześnie. Uruchamiaj sekwencyjnie.
- **Fine-tuning 7B:** Wymaga min. 11GB VRAM (QLoRA). Użyj Google Colab (free, T4 15GB) lub Kaggle (free, P100) do trenowania, potem wróć z GGUF do Ollama.
- **Fine-tuning małych modeli lokalnie:** TinyLlama (1.1B), phi-2 (2.7B) — możliwe na 6GB z Unsloth.

## NER Labels (spaCy pl_core_news_lg)

Model używa formatu NKJP — **nie** standardowego PER/ORG/LOC:
- `persName` — osoby
- `orgName` — organizacje
- `placeName` — miejsca
- `geogName` — obiekty geograficzne
- `date` — daty
- `time` — czas

## Ollama modele (już zainstalowane)

```
bielik:Q4_K_S    4.1GB  ← główny model do RAG i Q&A po polsku
qwen-pl:latest   4.7GB  ← alternatywa, lepsza ogólna znajomość PL
moondream        1.7GB  ← analiza zdjęć i dokumentów wizualnych
```

Pobieranie LLaVA (opcjonalne, pełne 4.7GB):
```bash
ollama pull llava:7b
```

## Pierwsze kroki

1. Wrzuć kilka plików PDF do `C:\Users\rzecz\AI-Dziennikarstwo\archiwum\`
2. Uruchom `URUCHOM.bat` → opcja 1 (Web UI)
3. W Web UI: zakładka "Indeksuj dokumenty" → kliknij "Indeksuj"
4. Zakładka "Przeszukaj archiwum" → zadaj pytanie po polsku

## Real-ESRGAN (instalacja opcjonalna)

```bash
# W venv ai-pipeline (może wymagać Visual C++ Build Tools)
pip install realesrgan basicsr
```
Potem: `python restauracja_mediow.py obraz stary_skan.jpg`
