"""
Graf powiązań OSINT — NetworkX + PyVis
Buduje interaktywny graf z wyników NER pipeline.

Użycie:
  from pipeline import kolekcja
  from graf_powiazań import buduj_graf, wizualizuj
"""

import json
import pathlib
import networkx as nx
from pyvis.network import Network

from czarneniebo.config import WYNIKI_DIR


def buduj_graf(kolekcja) -> nx.DiGraph:
    """
    Buduje graf powiązań z danych NER z ChromaDB.
    Węzły: osoby i organizacje.
    Krawędzie: osoba → organizacja (z dokumentu źródłowego).
    """
    G = nx.DiGraph()

    wyniki = kolekcja.get(include=["metadatas"])
    metadane = wyniki["metadatas"]

    for meta in metadane:
        plik = meta.get("plik", "?")
        osoby = json.loads(meta.get("osoby", "[]"))
        organizacje = json.loads(meta.get("organizacje", "[]"))
        miejsca = json.loads(meta.get("miejsca", "[]"))

        # Węzły: osoby (kolor niebieski), org (kolor pomarańczowy), miejsca (zielony)
        for osoba in osoby:
            if osoba and not G.has_node(osoba):
                G.add_node(osoba, typ="osoba", color="#4e9af1", size=20, title=f"Osoba\nŹródło: {plik}")

        for org in organizacje:
            if org and not G.has_node(org):
                G.add_node(org, typ="organizacja", color="#f18b4e", size=25, title=f"Organizacja\nŹródło: {plik}")

        for miejsce in miejsca:
            if miejsce and not G.has_node(miejsce):
                G.add_node(miejsce, typ="miejsce", color="#4ef15a", size=15, title=f"Miejsce\nŹródło: {plik}")

        # Krawędzie: osoba → organizacja (współwystępowanie w dokumencie)
        for osoba in osoby:
            for org in organizacje:
                if osoba and org:
                    if G.has_edge(osoba, org):
                        G[osoba][org]["weight"] += 1
                        G[osoba][org]["pliki"].append(plik)
                    else:
                        G.add_edge(osoba, org, weight=1, pliki=[plik], label="powiązany_z")

        # Osoba → Miejsce
        for osoba in osoby:
            for miejsce in miejsca:
                if osoba and miejsce:
                    if not G.has_edge(osoba, miejsce):
                        G.add_edge(osoba, miejsce, weight=1, pliki=[plik], label="w_miejscu")

    return G


def statystyki_grafu(G: nx.DiGraph) -> dict:
    """Zwraca kluczowe statystyki grafu."""
    return {
        "wezly": G.number_of_nodes(),
        "krawedzie": G.number_of_edges(),
        "osoby": sum(1 for n, d in G.nodes(data=True) if d.get("typ") == "osoba"),
        "organizacje": sum(1 for n, d in G.nodes(data=True) if d.get("typ") == "organizacja"),
        "najbardziej_polaczone": sorted(
            G.degree(), key=lambda x: x[1], reverse=True
        )[:10],
    }


def znajdz_polaczenia(G: nx.DiGraph, podmiot: str, glebokosc: int = 2) -> list:
    """Znajdź wszystkich powiązanych z danym podmiotem do zadanej głębokości."""
    if podmiot not in G:
        # Szukaj częściowego dopasowania
        pasujace = [n for n in G.nodes() if podmiot.lower() in n.lower()]
        if not pasujace:
            return []
        podmiot = pasujace[0]
        print(f"Znaleziono: {podmiot}")

    powiazane = list(nx.ego_graph(G, podmiot, radius=glebokosc).nodes())
    return [n for n in powiazane if n != podmiot]


def wizualizuj(
    G: nx.DiGraph,
    plik_wyjsciowy: str = "graf_powiazań.html",
    filtr_podmiot: str | None = None,
    glebokosc: int = 2,
) -> str:
    """
    Generuje interaktywną wizualizację HTML.

    Args:
        G: Graf NetworkX
        plik_wyjsciowy: Ścieżka do pliku HTML
        filtr_podmiot: Jeśli podany, pokaż tylko otoczenie tego podmiotu
        glebokosc: Głębokość otoczenia przy filtrze
    """
    if filtr_podmiot:
        pasujace = [n for n in G.nodes() if filtr_podmiot.lower() in n.lower()]
        if pasujace:
            podmiot = pasujace[0]
            G = G.subgraph(list(nx.ego_graph(G, podmiot, radius=glebokosc).nodes()))

    net = Network(
        height="800px",
        width="100%",
        directed=True,
        bgcolor="#1a1a2e",
        font_color="white",
        notebook=False,
    )
    net.from_nx(G)

    # Opcje fizyki dla czytelniejszego układu
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100
        },
        "solver": "forceAtlas2Based",
        "minVelocity": 0.75
      }
    }
    """)

    sciezka = str(WYNIKI_DIR / plik_wyjsciowy)
    WYNIKI_DIR.mkdir(exist_ok=True)
    net.save_graph(sciezka)
    print(f"Graf zapisany: {sciezka}")
    print(f"Otwórz w przeglądarce: file:///{sciezka.replace(chr(92), '/')}")
    return sciezka


if __name__ == "__main__":
    print("Moduł grafu powiązań gotowy.")
    print("Użycie:")
    print("  from pipeline import kolekcja")
    print("  G = buduj_graf(kolekcja)")
    print("  print(statystyki_grafu(G))")
    print("  wizualizuj(G)")
    print("  znajdz_polaczenia(G, 'Kowalski')")
