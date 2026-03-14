# AUDYT CZARNE NIEBO AI — 2026-03-14

> Wygenerowany przez rój 5 agentów Claude Cowork. Czas audytu: ~15 minut.
> Misja: read-only. Żadne pliki nie zostały zmodyfikowane.

---

## 1. Stan kodu (Agent 1)

**Projekt:** `czarneniebo-ai v0.1.0`, Python 3.10
**Repozytorium:** github.com/lehorhe/czarneniebo-ai
**Struktura:** Pakiet `czarneniebo/` z 9 modułami (~1928 linii kodu)

### Moduły wdrożone
- `pipeline.py` — RAG + ChromaDB + spaCy (architektura centralna)
- `dezinformacja.py` — klasyfikacja i analiza (sentence-transformers + LogisticRegression, 0.002s/artykuł)
- `web_ui.py` — interfejs Gradio (5 zakładek, lazy loading)
- `graf_powiazań.py` — wizualizacja NetworkX + PyVis
- `file_watcher.py` — monitoring zmian (watchdog)
- `whisper_transkrypcja.py` — transkrypcja audio (faster-whisper)
- `restauracja_mediow.py` — odbudowa mediów (Demucs, Real-ESRGAN, GFPGAN)
- `forensics_pipeline.py` — **PREMIUM** — detekcja deepfake (5 sygnałów: ELA, metadata, NN, twarz, temporal)
- `config.py` — konfiguracja przez zmienne środowiskowe (wzorcowy pattern)

### Ocena jakości kodu
- **Kompletność:** 9/10 — wszystkie zaplanowane moduły zaimplementowane
- **Jakość:** 9/10 — lazy loading, config-driven, brak hardcoded paths w logice
- **Testy:** 41 passed (działają bez GPU/Ollama — smart design)
- **Architektura:** 10/10 — config.py jako Single Source of Truth, cross-platform

### Problemy z kodem
- **Legacy root-level:** `pipeline.py`, `dezinformacja.py`, `web_ui.py` etc. w korzeniu repo — stare kopie do usunięcia (zaznaczone w `.gitignore`)
- **Uncommitted:** 5 plików z ~760 zmianami białych znaków (formatowanie IDE, niebloking)
- **`.github/workflows/`:** stworzony ale NIE committed
- **Brak znalezionego bugu** `except Importers if False else Exception` — albo usunięty, albo nie dotyczył aktualnej wersji

---

## 2. Stan infrastruktury (Agent 2)

**Hardware:** GTX 1660 SUPER 6.4GB VRAM, i5-12400F, 16GB RAM, 153GB wolne
**venv:** `C:\Users\rzecz\ai-pipeline\`, Python 3.10.11

### Zależności — status

| Pakiet | Wersja | Status |
|--------|--------|--------|
| PyTorch | 2.5.1 + CUDA 12.1 | ✓ |
| spaCy | 3.8.11 + pl_core_news_lg | ✓ |
| Ollama client | 0.6.1 | ✓ |
| faster-whisper | 1.2.1 | ✓ |
| ChromaDB | 1.5.5 | ✓ |
| sentence-transformers | 5.3.0 (CPU) | ✓ |
| Gradio | 6.9.0 | ✓ |
| transformers | 5.3.0 | ✓ |
| demucs | 4.0.1 | ✓ |
| facenet-pytorch | — | ✓ |
| easyocr | 1.7.2 | ✓ |

**Wszystkie core + premium zależności zainstalowane.** Brak braków.

### Ollama — modele
- `bielik-7b-instruct-v0.1-gguf` (Q4/Q5) — główny LLM (polski)
- `qwen-pl` — multilingual instruct
- `qwen2.5` — 7B base
- `moondream` — vision model (forensics)
- **Łącznie: ~15 GB**

### Kluczowe optymalizacje
- sentence-transformers wymuszony na CPU (commit `309c01b`) — zwalnia VRAM dla Ollama/Bielika
- Brak pliku `.env` — config przez zmienne środowiskowe `CN_*`

### Wymagane zmienne środowiskowe

| Zmienna | Default | Opis |
|---------|---------|------|
| `CN_BASE_DIR` | `~/czarneniebo-data` | Katalog bazowy |
| `CN_OLLAMA_MODEL` | `bielik-7b-instruct...Q4_K_S` | Główny LLM |
| `CN_OLLAMA_EMBED` | `bge-m3` | Embeddings |
| `CN_OLLAMA_VISION` | `moondream` | Vision |
| `CN_WHISPER_MODEL` | `medium` | Model Whisper |
| `CN_WHISPER_DEVICE` | `cuda` | Device GPU/CPU |
| `CN_UI_PORT` | `7860` | Port Gradio UI |

### Uwagi
- Drugi venv `myenv/` istnieje ale nieużywany (do usunięcia)
- Brak CPU fallback dla Whisper przy CUDA OOM (ryzyko!)

---

## 3. Stan dokumentacji (Agent 3)

### Ocena plików

| Plik | Ocena | Status |
|------|-------|--------|
| `README.md` | 9/10 | Kompletny, brak badge'ów |
| `docs/index.md` | 8/10 | Dobry overview |
| `docs/instalacja.md` | 9/10 | Szczegółowa, aktualna |
| `docs/licencja.md` | 7/10 | OK, ale blockchain placeholder |
| `mkdocs.yml` | 5/10 | **Błędne URL!** |
| `URUCHOM.bat` | 7/10 | Odwołuje się do legacy plików |
| `LICENSE` | 9/10 | Kompletny Apache 2.0 |
| `LICENSE-PREMIUM` | 7/10 | Placeholder `[CONTRACT_ADDRESS]` |
| `.github/workflows/docs.yml` | 8/10 | Dobry, ale NIE committed |
| `.github/workflows/release.yml` | 6/10 | Bug: `main` zamiast `master` |

### Krytyczne błędy dokumentacji

| # | Problem | Lokalizacja | Naprawa |
|---|---------|-------------|---------|
| 1 | `site_url: czarneniebo.github.io` | `mkdocs.yml` L3 | → `lehorhe.github.io` |
| 2 | `repo_url: czarneniebo/czarneniebo-ai` | `mkdocs.yml` L4 | → `lehorhe/czarneniebo-ai` |
| 3 | Nav referencuje `docs/api/*.md` | `mkdocs.yml` nav | Stubs lub usunąć z nav |
| 4 | `.github/workflows/` nie committed | git status | `git add .github && git commit` |
| 5 | `release.yml` używa `main` | `.github/workflows/release.yml` L34 | → `master` |
| 6 | `URUCHOM.bat` → `web_ui.py` (root) | `URUCHOM.bat` L17 | → `python -m czarneniebo.web_ui` |
| 7 | `dezinformacja.py` jako PREMIUM w docs | `README.md` | Ujednolicić (Apache 2.0) |
| 8 | `[CONTRACT_ADDRESS]` placeholder | `LICENSE-PREMIUM` | Wypełnić lub usunąć sekcję blockchain |

---

## 4. Zasoby do wykorzystania (Agent 4)

### Materiały testowe — klasyfikacja

#### 🟢 Klasa A — gotowe do testów MVP

| Materiał | Rozmiar | Typ | Użycie w pipeline |
|----------|---------|-----|-------------------|
| `CN-SF Szkolenie/` (6× MP4) | 2.0 GB | Video sesji Stop Fake | **Whisper transkrypcja** |
| `Videos/Czarne Niebo Po Ukraińsku.mp4` | 200 MB | Audycja radiowa | Test Whisper PL |
| `Videos/Wywiad2a.mp4` | 856 MB | Wywiad long-form | **Stress test pipeline** |
| `Documents/OPCJE/` (MP3 + HTML + TXT) | 434 MB | ZOOM z gotowymi transkryptami | **Walidacja RAG** |

**Łącznie: ~3.5 GB gotowych materiałów testowych**

#### 🟡 Klasa B — wsparcie

| Materiał | Rozmiar | Użycie |
|----------|---------|--------|
| `Documents/Zakarpacie/` (17 PNG) | 36 MB | Test OCR |
| `Documents/Przybysz_ksiazka/` (18 DOCX) | 39 MB | Pipeline DOCX |
| `gen_article.py` (358 linii) | 35 KB | Wzorzec generatora HTML |
| `korektor_ai_v3.py` (Gemini + Track Changes) | ~244 linii | Wzorzec AI redakcji |

### Kluczowe odkrycie: OPCJE/
Folder `Documents/OPCJE/` zawiera MP3 + gotowe HTML transkrypcje + TXT + PDF — **idealny do walidacji RAG** (mamy input i oczekiwany output).

---

## 5. Strategia rozwoju (Agent 5)

### 5.1 Ocena gotowości MVP

**Definicja MVP:** Pipeline działa end-to-end (audio → transkrypcja → analiza → raport), UI użyteczne, instalacja powtarzalna.

| Komponent | Gotowość | Uwagi |
|-----------|----------|-------|
| Kod | ✓ 95% | Cleanup legacy + commit workflows |
| Infrastruktura | ✓ 95% | Brak CPU fallback Whisper |
| Dokumentacja instalacji | ✗ 60% | 4 blokujące błędy w config |
| Materiały testowe | ✓ 100% | 3.5 GB gotowych zasobów |
| UI (Gradio) | ✓ 90% | Brak export PDF/DOCX |

### **GOTOWOŚĆ MVP: 7.5/10**

---

### 5.2 Top 5 blokujących problemów

| # | Problem | Plik | Naprawa | Czas |
|---|---------|------|---------|------|
| 1 | Błędne domeny w mkdocs.yml | `mkdocs.yml` L3-L5 | `czarneniebo.github.io` → `lehorhe.github.io` | 10 min |
| 2 | docs/api/ puste, referencowane w nav | `mkdocs.yml` + `docs/api/` | Stworzyć stubs lub usunąć z nav | 30 min |
| 3 | .github/workflows/ NIE committed | git | `git add .github && git commit` | 5 min |
| 4 | scripts/install.py nie istnieje | — | Napisać auto-installer (venv + pip + ollama pull) | 2h |
| 5 | URUCHOM.bat → legacy pliki | `URUCHOM.bat` | `python web_ui.py` → `python -m czarneniebo.web_ui` | 15 min |
| *Bonus* | Brak CPU fallback Whisper | `whisper_transkrypcja.py` | try/except CUDA → CPU | 30 min |

---

### 5.3 Plan testowania

**Scenariusz 1 — Whisper (1.5h):**
Input: `CN-SF Szkolenie/sesja1.mp4` (300MB)
Test: WER < 15%, VRAM < 80%, czas < 30s/min audio
Output: JSON z timestamps + tekst

**Scenariusz 2 — RAG walidacja (1.5h):**
Input: `OPCJE/` (TXT transkrypcje)
Test: Precision@3 > 70% na 10 query ręcznie ocenionych
Output: ChromaDB vector store

**Scenariusz 3 — Klasyfikacja dezinformacji (1.5h):**
Input: Transkrypcja z S1
Test: F1-score > 0.70 na 20 ręcznie anotowanych claims
Output: JSON claim→prediction

**Scenariusz 4 — UI end-to-end (1h):**
Input: `Videos/Czarne Niebo Po Ukraińsku.mp4`
Test: Brak crashów, progress bar, raport HTML w < 5 min
Output: Raport HTML w UI

**Scenariusz 5 — Stress test (2h):**
Input: `Videos/Wywiad2a.mp4` (856MB, ~1.5h)
Test: Brak CUDA OOM, VRAM peak < 6.0GB, czas < 15 min
Output: Kompletna transkrypcja

**Timeline: 3 dni (łącznie ~7.5h pracy)**

---

### 5.4 Model biznesowy — ocena

**Struktura:** Apache 2.0 (CORE free) + Commercial 500 PLN/rok (PREMIUM)
- PREMIUM: `forensics_pipeline.py` — detekcja deepfake

| Aspekt | Ocena | Komentarz |
|--------|-------|-----------|
| Cena 500 PLN/rok | ✓ Realna | Niskie vs rynkowe (Copyleaks ~2000 PLN/rok) |
| Podział core/premium | ✓ Ma sens | PREMIUM = high-value, wymaga continuous training |
| Akwizycja klientów | ⚠️ Ryzyko | Brak marketing planu, media w PL nie znają produktu |
| Wsparcie | ⚠️ Ryzyko | 1 deweloper = max ~50 klientów |
| Blockchain ERC-1155 | ❌ Upuść | Overkill, friction dla klientów, PL klienci = Stripe/PayU |

**Rekomendacja:** Upuścić blockchain z LICENSE-PREMIUM. Stripe/PayU + prosta walidacja klucza API.

---

### 5.5 Roadmap

| Wersja | Target | Fokus | Dev-time |
|--------|--------|-------|----------|
| **v0.1.0** | 2026-03-18 | Naprawy docs, scripts/install.py, testy E2E | 5-6 dni |
| **v0.2.0** | 2026-04/05 | Export PDF/DOCX, batch processing, REST API | 14 dni |
| **v0.3.0** | 2026-06 | Premium forensics, auth, Docker, beta launch | 16 dni + 14 dni beta |
| **v1.0.0** | 2026-09 | SaaS, monitoring, ≥50 paying customers | Po adopcji |

**Założenie:** 1 developer, 50% czasu na projekt. Slip +4-8 tygodni na każdą wersję.

---

### 5.6 Ryzyka techniczne

| # | Ryzyko | Wpływ | Mitigation |
|---|--------|-------|-----------|
| 1 | **CUDA OOM na dużym audio** (6.4GB VRAM) | Crash pipeline | CPU fallback dla Whisper, sekwencyjne ładowanie |
| 2 | **Brak CPU mode Whisper** | Brak fallback | Dodać `try: device="cuda" except: device="cpu"` |
| 3 | **Dependency versioning** | Instalacja na nowych systemach | Docker image z pinned versions |
| 4 | **spaCy pl_core_news_lg słownictwo AI** | Niska accuracy NER na nowych terminach | Fine-tuning lub augmentation |
| 5 | **ChromaDB embeddings staleness** | Nieaktualne wyniki RAG | Incremental refresh 24h |

---

### 5.7 Metryki sukcesu beta (v0.3.0)

**Techniczne:**

| Metryka | Target |
|---------|--------|
| Whisper WER | < 15% |
| RAG Precision@3 | > 70% |
| Claim classification F1 | > 0.70 |
| VRAM peak | < 6.0 GB |
| Processing time/min audio | < 0.5 min |
| Uptime (beta) | > 95% |

**Biznesowe:**

| Metryka | Target |
|---------|--------|
| Beta signups | ≥ 50 |
| Activation rate | ≥ 40% |
| Premium conversion | ≥ 10% |
| NPS | ≥ 30 |

---

## PODSUMOWANIE WYKONAWCZE

### Gotowość MVP: **7.5/10**

Kod i infrastruktura są gotowe (9/10). Blokuje dokumentacja (4 błędy w konfiguracji mkdocs + brak scripts/install.py).

---

### Blokujące problemy (do MVP)

1. ❌ `mkdocs.yml` — domeny `czarneniebo.github.io` → `lehorhe.github.io` (10 min)
2. ❌ `docs/api/` — puste, nav je referencuje → stubs lub usunąć (30 min)
3. ❌ `.github/workflows/` — nie committed (5 min)
4. ❌ `scripts/install.py` — nie istnieje, obiecany w README (2h)
5. ⚠️ `URUCHOM.bat` — legacy paths, zepsuje instalację (15 min)

**Łączny czas napraw: ~3h roboczych**

---

### Następne kroki (priorytet)

| # | Task | Deadline | Czas |
|---|------|----------|------|
| 1 | Naprawić mkdocs.yml (domeny + repo_url) | 2026-03-15 | 15 min |
| 2 | Stworzyć docs/api/ stubs lub usunąć z nav | 2026-03-15 | 30 min |
| 3 | `git add .github && git commit` | 2026-03-15 | 5 min |
| 4 | Napisać scripts/install.py | 2026-03-16 | 2h |
| 5 | Testy E2E: S1+S2+S3 (CN-SF + OPCJE) | 2026-03-17 | 4.5h |

---

### Szacowany czas do MVP

- **v0.1.0 release-ready:** 2026-03-18 (naprawy dokumentacji ~3h + testy 4.5h)
- **v0.3.0 beta launch:** 2026-06-15 (+11 tygodni przy 50% czasu na projekt)

---

*Audyt wykonany 2026-03-14 przez rój 5 agentów Claude Cowork.*
*Repozytorium: github.com/lehorhe/czarneniebo-ai*
