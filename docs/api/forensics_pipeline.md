# czarneniebo.forensics_pipeline

Wielosygnałowy detektor autentyczności mediów (PREMIUM).

!!! note "Documentation in progress"
    Pełna dokumentacja jest w przygotowaniu.

## Klasy

### `Sygnal`

```python
@dataclass
class Sygnal:
    nazwa: str
    wynik: float        # 0.0 = fałszywy, 1.0 = autentyczny
    pewnosc: float      # 0.0–1.0
    opis: str
    szczegoly: dict
    blad: Optional[str]
```

### `ForensicsRaport`

```python
@dataclass
class ForensicsRaport:
    poziom_pewnosci: float
    etykieta: str
    sygnaly: dict[str, Sygnal]
    zalecenie: str
    plik: str
    hash_md5: str
    timestamp: str

    def jako_dict(self) -> dict
    def html(self) -> str
```

### `ForensicsAnalyzer`

```python
class ForensicsAnalyzer:
    def analizuj(self, sciezka: str | pathlib.Path) -> ForensicsRaport
    def zapisz_raport(self, raport: ForensicsRaport, folder: pathlib.Path = None) -> pathlib.Path
```

::: czarneniebo.forensics_pipeline
