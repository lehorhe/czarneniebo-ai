# Czarne Niebo AI

**Narzędzia AI dla dziennikarstwa śledczego i weryfikacji mediów**

*Stop Fake / Czarne Niebo — Lech Rustecki*

---

## Co to jest?

Czarne Niebo AI to otwartoźródłowy zestaw narzędzi AI przeznaczony dla dziennikarzy śledczych, weryfikatorów faktów i analityków mediów. Zbudowany na lokalnych modelach językowych (bez chmury, bez wysyłania danych) z myślą o bezpieczeństwie pracy dziennikarskiej.

## Możliwości

=== "Core (bezpłatne)"
    - **Archiwum RAG** — semantyczne przeszukiwanie dokumentów z odpowiedziami Bielika
    - **Transkrypcja** — Whisper medium, język polski, nagrania archiwalne
    - **Graf OSINT** — interaktywny graf powiązań osobowych i organizacyjnych
    - **NER** — automatyczne wyciąganie osób, org, miejsc z dokumentów PDF

=== "Premium (licencja)"
    - **Forensics** — wielosygnałowy detektor autentyczności (ELA, EXIF, NN, twarze, temporal)
    - **Dezinformacja** — hybrydowy klasyfikator ML (1000x szybszy niż LLM)
    - **Restauracja mediów** — Demucs + Real-ESRGAN dla archiwalii

## Szybki start

```bash
# Windows
git clone https://github.com/czarneniebo/czarneniebo-ai
cd czarneniebo-ai
python scripts/install.py
```

Otwórz `http://localhost:7860` po instalacji.

## Wymagania sprzętowe

| Komponent | Minimum | Testowane |
|-----------|---------|-----------|
| GPU | NVIDIA 4GB VRAM | GTX 1660 SUPER 6GB |
| RAM | 8 GB | 16 GB |
| Dysk | 20 GB wolne | SSD zalecane |
| Python | 3.10+ | 3.10.11 |
| CUDA | 11.8+ | 12.1 |

## Architektura

```
Archiwum na dysku → File Watcher → Pipeline multimodalny
                                   ├── PDF → pdfplumber/EasyOCR
                                   ├── Audio → Whisper medium
                                   └── Obraz → EasyOCR/LLaVA
                                        ↓
                                   spaCy NER → ChromaDB
                                        ↓
                                   Gradio UI ← Dziennikarz
                                        ↓
                                   Bielik RAG → Odpowiedź
                                        ↓
                                   NetworkX → Graf powiązań
```

## Licencja

- **Core modules**: Apache 2.0 — wolny dostęp, modyfikacja, redystrybucja
- **Premium modules**: Licencja komercyjna — [szczegóły](licencja.md)
