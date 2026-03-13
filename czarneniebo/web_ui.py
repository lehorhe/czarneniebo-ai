"""
Czarne Niebo AI — Web UI (PUBLIC)
===================================
Gradio interface — jeden punkt wejścia dla całego systemu.

Uruchomienie:
    set CN_BASE_DIR=C:/Users/rzecz/AI-Dziennikarstwo
    C:/Users/rzecz/ai-pipeline/Scripts/python.exe -m czarneniebo.web_ui
    → http://localhost:7860

Lub przez skrypt:
    python scripts/run_ui.py
"""

import pathlib
import json
import gradio as gr

from czarneniebo.config import (
    ARCHIWUM_DIR, WYNIKI_DIR, OLLAMA_MODEL_CHAT,
    UI_HOST, UI_PORT, VERSION, PROJECT_NAME
)

# Lazy imports — przyspiesza start UI
_pipeline = None
_forensics = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from czarneniebo import pipeline
        _pipeline = pipeline
    return _pipeline


def _get_forensics():
    global _forensics
    if _forensics is None:
        from czarneniebo.forensics_pipeline import ForensicsAnalyzer
        _forensics = ForensicsAnalyzer()
    return _forensics


# ── zakładka: Archiwum ────────────────────────────────────────

def interfejs_szukaj(pytanie: str):
    if not pytanie.strip():
        return "Wpisz pytanie.", ""
    p = _get_pipeline()
    if p.kolekcja.count() == 0:
        return "Archiwum puste — użyj zakładki 'Indeksuj'.", ""
    odpowiedz = p.zapytaj_archiwum(pytanie, n_kontekst=3)
    trafienia = p.szukaj(pytanie, n=5)
    zrodla = "\n".join(
        f"**[{t['odleglosc']:.3f}] {t['plik']}**\n"
        f"Osoby: {', '.join(t['osoby'][:5]) or '—'} | "
        f"Org: {', '.join(t['organizacje'][:5]) or '—'}"
        for t in trafienia
    )
    return odpowiedz, zrodla


def interfejs_indeksuj(folder: str):
    sciezka = pathlib.Path(folder.strip())
    if not sciezka.exists():
        return f"Folder nie istnieje: {sciezka}"
    p = _get_pipeline()
    try:
        p.indeksuj_folder(sciezka)
        return f"Zaindeksowano. Dokumentów w bazie: {p.kolekcja.count()}"
    except Exception as e:
        return f"Błąd: {e}"


def interfejs_transkrybuj(plik_audio):
    if plik_audio is None:
        return "Wgraj plik audio."
    from czarneniebo.whisper_transkrypcja import transkrybuj
    wynik = transkrybuj(plik_audio, jezyk="pl")
    return wynik["tekst"]


def interfejs_status():
    try:
        p = _get_pipeline()
        return f"Dokumentów w bazie: {p.kolekcja.count()} | Model: {OLLAMA_MODEL_CHAT}"
    except Exception as e:
        return f"Pipeline nie załadowany ({e})"


def interfejs_graf(podmiot: str):
    from czarneniebo.graf_powiazań import buduj_graf, wizualizuj, znajdz_polaczenia
    p = _get_pipeline()
    G = buduj_graf(p.kolekcja)
    if podmiot.strip():
        sciezka = wizualizuj(G, "graf_powiazań.html", filtr_podmiot=podmiot.strip())
        powiazane = znajdz_polaczenia(G, podmiot.strip())
        return (f"Graf: {sciezka}\n\nPowiązane z '{podmiot}':\n"
                + "\n".join(f"• {x}" for x in powiazane[:20]))
    else:
        sciezka = wizualizuj(G, "graf_powiazań.html")
        return f"Graf pełny: {sciezka}\nWęzłów: {G.number_of_nodes()}, krawędzi: {G.number_of_edges()}"


# ── zakładka: Forensics (PREMIUM) ────────────────────────────

def interfejs_forensics(plik_media):
    """Analiza autentyczności — wielosygnałowy detektor."""
    if plik_media is None:
        return "Wgraj plik (JPG, PNG, MP4).", "", ""

    try:
        analyzer = _get_forensics()
        raport = analyzer.analizuj(plik_media)
        html_path = analyzer.zapisz_raport(raport)

        # Skrócony wynik dla UI
        kolor = {
            "PRAWDOPODOBNIE_AUTENTYCZNY": "🟢",
            "WYMAGA_WERYFIKACJI": "🟡",
            "PODEJRZANY": "🔴",
        }.get(raport.etykieta, "⚪")

        wynik_txt = (
            f"{kolor} **{raport.etykieta.replace('_', ' ')}**\n"
            f"Poziom autentyczności: **{raport.poziom_pewnosci:.0%}**\n\n"
            f"**Zalecenie:** {raport.zalecenie}"
        )

        sygnaly_txt = "\n".join(
            f"**{n.upper()}** ({s.wynik:.0%}): {s.opis}"
            + (f"\n  ⚠ Błąd: {s.blad}" if s.blad else "")
            for n, s in raport.sygnaly.items()
        )

        return wynik_txt, sygnaly_txt, f"Raport HTML: {html_path}"

    except Exception as e:
        return f"Błąd analizy: {e}", "", ""


# ── budowa UI ─────────────────────────────────────────────────

with gr.Blocks(
    title=f"{PROJECT_NAME} v{VERSION}",
) as app:

    gr.Markdown(f"""
    # {PROJECT_NAME} v{VERSION}
    *GTX 1660 SUPER · Bielik 7B · spaCy PL · ChromaDB · Stop Fake / Czarne Niebo*
    """)

    with gr.Tab("Przeszukaj archiwum"):
        with gr.Row():
            with gr.Column():
                pytanie_inp = gr.Textbox(
                    label="Pytanie",
                    placeholder="Kto jest powiązany ze spółką X? Jakie dokumenty dotyczą Jana Kowalskiego?",
                    lines=3,
                )
                szukaj_btn = gr.Button("Zapytaj Bielika", variant="primary")
                gr.Textbox(label="Status", value=interfejs_status, interactive=False)
            with gr.Column():
                odpowiedz_out = gr.Textbox(label="Odpowiedź Bielika", lines=10)
                zrodla_out = gr.Markdown(label="Źródła")
        szukaj_btn.click(interfejs_szukaj, [pytanie_inp], [odpowiedz_out, zrodla_out])
        pytanie_inp.submit(interfejs_szukaj, [pytanie_inp], [odpowiedz_out, zrodla_out])

    with gr.Tab("Indeksuj dokumenty"):
        gr.Markdown("Podaj ścieżkę do folderu z dokumentami (PDF, JPG, PNG, TXT).")
        folder_inp = gr.Textbox(label="Folder", value=str(ARCHIWUM_DIR))
        gr.Button("Indeksuj", variant="primary").click(
            interfejs_indeksuj, [folder_inp], [gr.Textbox(label="Wynik")]
        )

    with gr.Tab("Transkrypcja audio"):
        gr.Markdown("Whisper medium, język polski. Działa na GPU ~3GB VRAM.")
        audio_inp = gr.Audio(type="filepath", label="Plik audio/video")
        transkrybuj_btn = gr.Button("Transkrybuj", variant="primary")
        transkrypcja_out = gr.Textbox(label="Transkrypcja", lines=15)
        transkrybuj_btn.click(interfejs_transkrybuj, [audio_inp], [transkrypcja_out])

    with gr.Tab("Graf powiązań OSINT"):
        podmiot_inp = gr.Textbox(label="Filtruj po podmiocie (opcjonalnie)")
        gr.Button("Generuj graf", variant="primary").click(
            interfejs_graf, [podmiot_inp], [gr.Textbox(label="Wynik", lines=10)]
        )

    with gr.Tab("Forensics — Weryfikacja mediów"):
        gr.Markdown("""
        ### Wielosygnałowy detektor autentyczności
        **Sygnały:** ELA · Metadane EXIF · Model NN · Analiza twarzy · Temporal video

        ⚠ *Wynik to "waga dowodów", nie wyrok. Decyzja zawsze należy do dziennikarza.*
        """)
        media_inp = gr.File(label="Wgraj plik (JPG, PNG, MP4, AVI)", type="filepath")
        forensics_btn = gr.Button("Analizuj autentyczność", variant="primary")
        with gr.Row():
            wynik_out = gr.Markdown(label="Wynik")
            sygnaly_out = gr.Markdown(label="Sygnały szczegółowe")
        raport_out = gr.Textbox(label="Raport zapisany w")
        forensics_btn.click(
            interfejs_forensics, [media_inp], [wynik_out, sygnaly_out, raport_out]
        )

    gr.Markdown(f"""
    ---
    [Patronite](https://patronite.pl/CzarneNiebo) · [Stop Fake](https://stopfake.org/pl/) ·
    Apache 2.0 (core) / Commercial (premium) · v{VERSION}
    """)


def main():
    app.launch(
        server_name=UI_HOST,
        server_port=UI_PORT,
        share=False,
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 1200px; margin: auto; }",
    )


if __name__ == "__main__":
    main()
