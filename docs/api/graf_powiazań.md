# czarneniebo.graf_powiazań

Graf powiązań OSINT — NetworkX + PyVis.

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Funkcje

```python
def buduj_graf(kolekcja) -> nx.DiGraph

def statystyki_grafu(G: nx.DiGraph) -> dict

def znajdz_polaczenia(G: nx.DiGraph, podmiot: str, glebokosc: int = 2) -> list

def wizualizuj(
    G: nx.DiGraph,
    plik_wyjsciowy: str = "graf_powiazań.html",
    filtr_podmiot: str | None = None,
    glebokosc: int = 2,
) -> str
```

::: czarneniebo.graf_powiazań
