# czarneniebo.pipeline

AI Pipeline dla dziennikarstwa śledczego — ekstrakcja tekstu, NER, embedding, RAG.

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Funkcje

```python
def doc_id(sciezka: pathlib.Path) -> str
def ekstrakcja_tekstu(sciezka: pathlib.Path) -> str
def ekstrakcja_ocr(sciezka: pathlib.Path) -> str
def ner_ekstrakcja(tekst: str) -> dict
def indeksuj_dokument(sciezka: pathlib.Path) -> dict
def indeksuj_folder(folder: pathlib.Path = ARCHIWUM_DIR) -> None
def szukaj(pytanie: str, n: int = 5) -> list[dict]
def zapytaj_archiwum(pytanie: str, n_kontekst: int = 3) -> str
```

::: czarneniebo.pipeline
