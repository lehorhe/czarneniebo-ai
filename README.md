# Czarne Niebo AI — Archiwum Dziennikarskie

**Narzędzie dla dziennikarzy śledczych i fact-checkerów**
**GTX 1660 SUPER 6GB · i5-12400F · 16GB RAM · Windows 11**

---

## Czym jest Czarne Niebo AI?

Lokalny pipeline AI do pracy z archiwum dziennikarskim:
- przeszukiwanie setek dokumentów PDF/audio/video po polsku (RAG)
- transkrypcja nagrań archiwalnych (Whisper)
- graf powiązań osoby–organizacje–miejsca (OSINT)
- **weryfikacja autentyczności mediów** — 5-sygnałowy detektor deepfake'ów

Działa lokalnie, bez chmury, na sprzęcie klasy gaming PC.

---

## Szybki start

```bat
# Kliknij dwukrotnie:
URUCHOM.bat

# Lub aktywuj ręcznie i uruchom Web UI:
C:\Users\rzecz\ai-pipeline\Scripts\activate.bat
python -m czarneniebo.web_ui
```

Interfejs działa pod: **http://localhost:7860**

---

## Struktura projektu

```
AI-Dziennikarstwo/
├── czarneniebo/
│   ├── config.py              ← ścieżki i stałe (CN_BASE_DIR)
│   ├── pipeline.py            ← OCR + NER + ChromaDB + RAG
│   ├── whisper_transkrypcja.py← audio/video → tekst (Whisper medium PL)
│   ├── graf_powiazań.py       ← graf OSINT (NetworkX + PyVis)
│   ├── dezinformacja.py       ← klasyfikator dezinformacji [PREMIUM]
│   ├── restauracja_mediow.py  ← Demucs + Real-ESRGAN [PREMIUM]
│   ├── forensics_pipeline.py  ← detektor deepfake'ów [PREMIUM]
│   ├── file_watcher.py        ← auto-indeksowanie archiwum
│   └── web_ui.py              ← Gradio UI
├── docs/                      ← dokumentacja (mkdocs)
├── archiwum/                  ← TU wrzucaj dokumenty
├── wyniki/                    ← wyniki pipeline, raporty HTML
├── archiwum_db/               ← ChromaDB (baza wektorowa)
└── modele/                    ← zapisane modele sklearn
```

---

## Komponenty

| Komponent | Zadanie | GPU/CPU |
|-----------|---------|---------|
| Ollama + Bielik Q4_K_S | Odpowiedzi po polsku (RAG) | GPU 4.1GB |
| Ollama + Moondream | Opisy i analiza zdjęć | GPU 1.7GB |
| faster-whisper medium | Transkrypcja PL | GPU ~3GB |
| Real-ESRGAN | Upscaling skanów 4x | GPU (kafelki) |
| Demucs | Separacja głosu z szumu | CPU/GPU |
| dima806/deepfake detector | Detekcja deepfake'ów (NN) | CPU |
| facenet-pytorch MTCNN | Analiza artefaktów twarzy | CPU |
| spaCy pl_core_news_lg | NER (NKJP: persName/orgName/placeName) | CPU |
| ChromaDB | Semantyczna baza wiedzy | CPU |
| sentence-transformers | Embeddingi multilingwalne | CPU |
| NetworkX + PyVis | Graf powiązań OSINT | CPU |
| Gradio Web UI | Interfejs dla dziennikarzy | - |

> **6GB VRAM:** Jeden duży model naraz. Bielik (4.1GB) + Whisper (~2GB) = za dużo jednocześnie. Uruchamiaj sekwencyjnie.

---

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

---

## Model licencyjny

| Tier | Zawartość | Cena |
|------|-----------|------|
| **CORE** | pipeline RAG, Whisper, OSINT, Web UI | Apache 2.0 — bezpłatnie |
| **PREMIUM** | forensics (deepfake), dezinformacja, restauracja mediów | ~500 PLN netto/rok |
| **ENTERPRISE** | admin access, SLA, sesje szkoleniowe | umowa indywidualna |

Kontakt: **czarneniebo@proton.me** · Patronite: **https://patronite.pl/CzarneNiebo**

---

## Pierwsze kroki

1. Wrzuć pliki PDF do `archiwum/`
2. Uruchom `URUCHOM.bat` → opcja 1 (Web UI)
3. Zakładka "Indeksuj dokumenty" → kliknij "Indeksuj"
4. Zakładka "Przeszukaj archiwum" → zadaj pytanie po polsku
5. Zakładka "Forensics" → wgraj zdjęcie/video do weryfikacji

---

## NER Labels (spaCy pl_core_news_lg)

Model używa formatu NKJP — **nie** standardowego PER/ORG/LOC:
- `persName` — osoby
- `orgName` — organizacje
- `placeName` — miejsca
- `geogName` — obiekty geograficzne
- `date` — daty
- `time` — czas

---

*Projekt: Czarne Niebo / Stop Fake — narzędzia dla dziennikarstwa śledczego*
