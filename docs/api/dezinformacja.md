# czarneniebo.dezinformacja

Detektor dezinformacji — sentence-transformers + Logistic Regression.

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Klasa `Detektor`

```python
class Detektor:
    def __init__(self, model_embeddingow: str = "paraphrase-multilingual-mpnet-base-v2")

    def trenuj(
        self,
        rzetelne: list[str],
        podejrzane: list[str],
        walidacja_krzyzowa: bool = True,
    ) -> dict

    def oceń(self, tekst: str) -> dict
    def oceń_batch(self, teksty: list[str]) -> list[dict]
    def zaladuj(self) -> bool
```

::: czarneniebo.dezinformacja
