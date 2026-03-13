"""
Detektor dezinformacji — Hybrid ML
sentence-transformers + Logistic Regression

Klasyczne ML: 0.002s/artykuł vs 2s dla LLM → 1000x szybciej, interpretowalnie.

Użycie:
  from dezinformacja import Detektor
  det = Detektor()
  det.trenuj(artykuly_rzetelne, artykuly_podejrzane)
  wynik = det.oceń("treść artykułu...")
"""

import pathlib
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report

MODEL_DIR = pathlib.Path("C:/Users/rzecz/AI-Dziennikarstwo/modele")
MODEL_DIR.mkdir(exist_ok=True)


class Detektor:
    """Detektor dezinformacji oparty na embeddingach + regresji logistycznej."""

    def __init__(self, model_embeddingow: str = "paraphrase-multilingual-mpnet-base-v2"):
        print(f"Ładowanie enkodera: {model_embeddingow}")
        self.enkoder = SentenceTransformer(model_embeddingow)
        self.klasyfikator = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",  # radzi sobie z niezbalansowanymi danymi
            C=1.0,
        )
        self.wytrenowany = False

    def _zakoduj(self, teksty: list[str]) -> np.ndarray:
        return self.enkoder.encode(teksty, show_progress_bar=True, batch_size=32)

    def trenuj(
        self,
        rzetelne: list[str],
        podejrzane: list[str],
        walidacja_krzyzowa: bool = True,
    ) -> dict:
        """
        Trenuje klasyfikator.

        Args:
            rzetelne: Lista artykułów uznanych za rzetelne (label=0)
            podejrzane: Lista artykułów podejrzanych o dezinformację (label=1)
            walidacja_krzyzowa: Czy przeprowadzić 5-fold cross-validation

        Returns:
            dict ze statystykami trenowania
        """
        print(f"Trenowanie na {len(rzetelne)} rzetelnych + {len(podejrzane)} podejrzanych")

        teksty = rzetelne + podejrzane
        etykiety = [0] * len(rzetelne) + [1] * len(podejrzane)

        print("Kodowanie embeddingów...")
        X = self._zakoduj(teksty)
        y = np.array(etykiety)

        if walidacja_krzyzowa and len(teksty) >= 10:
            wyniki_cv = cross_val_score(
                self.klasyfikator, X, y, cv=min(5, len(teksty) // 2), scoring="f1"
            )
            print(f"Cross-validation F1: {wyniki_cv.mean():.3f} ± {wyniki_cv.std():.3f}")

        self.klasyfikator.fit(X, y)
        self.wytrenowany = True

        # Ocena na danych treningowych (benchmark)
        pred = self.klasyfikator.predict(X)
        print(classification_report(y, pred, target_names=["Rzetelny", "Podejrzany"]))

        # Zapisz model
        sciezka = MODEL_DIR / "detektor_dezinformacji.pkl"
        with open(sciezka, "wb") as f:
            pickle.dump(self.klasyfikator, f)
        print(f"Model zapisany: {sciezka}")

        return {
            "przykladow": len(teksty),
            "rzetelnych": len(rzetelne),
            "podejrzanych": len(podejrzane),
        }

    def oceń(self, tekst: str) -> dict:
        """
        Ocenia pojedynczy artykuł.

        Returns:
            dict: {etykieta, pewnosc, rzetelny_prob, podejrzany_prob}
        """
        if not self.wytrenowany:
            raise RuntimeError("Model nie jest wytrenowany. Uruchom najpierw trenuj().")

        emb = self._zakoduj([tekst])
        proba = self.klasyfikator.predict_proba(emb)[0]
        etykieta = "PODEJRZANY" if proba[1] > 0.5 else "RZETELNY"

        return {
            "etykieta": etykieta,
            "pewnosc": float(max(proba)),
            "prob_rzetelny": float(proba[0]),
            "prob_podejrzany": float(proba[1]),
        }

    def oceń_batch(self, teksty: list[str]) -> list[dict]:
        """Ocenia listę artykułów (szybkie batchowe przetwarzanie)."""
        if not self.wytrenowany:
            raise RuntimeError("Model nie jest wytrenowany.")

        emb = self._zakoduj(teksty)
        proba = self.klasyfikator.predict_proba(emb)
        return [
            {
                "tekst_fragment": t[:100] + "...",
                "etykieta": "PODEJRZANY" if p[1] > 0.5 else "RZETELNY",
                "pewnosc": float(max(p)),
                "prob_podejrzany": float(p[1]),
            }
            for t, p in zip(teksty, proba)
        ]

    def zaladuj(self) -> bool:
        """Wczytuje zapisany model."""
        sciezka = MODEL_DIR / "detektor_dezinformacji.pkl"
        if not sciezka.exists():
            return False
        with open(sciezka, "rb") as f:
            self.klasyfikator = pickle.load(f)
        self.wytrenowany = True
        print(f"Model wczytany: {sciezka}")
        return True


# ── przykład: zestaw treningowy do szybkiego startu ──────────
PRZYKLADY_RZETELNE = [
    "Według oficjalnych danych GUS, inflacja w Polsce wyniosła w grudniu 3,2 proc. rok do roku.",
    "Ministerstwo Zdrowia potwierdziło rejestrację nowego leku po przejściu pełnej procedury klinicznej.",
    "Sąd Najwyższy wydał wyrok w sprawie, odwołując się do artykułu 190 Konstytucji RP.",
]

PRZYKLADY_PODEJRZANE = [
    "SZOKUJĄCE! Rząd ukrywa prawdę o szczepionkach! Podziel się zanim usuną!",
    "Naukowcy POTWIERDZAJĄ: chemtrails zatruwają wodę pitną. Mainstream media milczą!",
    "To co robi elita finansowa to LUDOBÓJSTWO. Budź się, owco!",
]


if __name__ == "__main__":
    det = Detektor()

    if not det.zaladuj():
        print("\nBrak zapisanego modelu. Trenowanie na przykładach demonstracyjnych...")
        print("(Dla produkcji: dostarcz setki/tysiące labeled artykułów)\n")
        det.trenuj(PRZYKLADY_RZETELNE, PRZYKLADY_PODEJRZANE, walidacja_krzyzowa=False)

    print("\nTest klasyfikatora:")
    test = "Eksperci z WHO ostrzegają przed nową falą chorób. Rządy ignorują zalecenia."
    wynik = det.oceń(test)
    print(f"Tekst: {test[:80]}...")
    print(f"Wynik: {wynik['etykieta']} (pewność: {wynik['pewnosc']:.0%})")
