"""
Web UI dla dziennikarzy — Gradio
Jeden punkt wejścia do całego systemu.

Uruchomienie:
  C:/Users/rzecz/ai-pipeline/Scripts/python.exe web_ui.py
  Otwórz: http://localhost:7860
"""

import gradio as gr
import json
import pathlib

# Lazy import pipeline żeby UI uruchamiał się szybko
_pipeline = None
_graf = None


def zaladuj_pipeline():
    global _pipeline
    if _pipeline is None:
        import pipeline as p
        _pipeline = p
    return _pipeline


def interfejs_szukaj(pytanie: str) -> tuple[str, str]:
    """Zakładka: Przeszukaj archiwum."""
    if not pytanie.strip():
        return "Wpisz pytanie.", ""
    p = zaladuj_pipeline()
    if p.kolekcja.count() == 0:
        return "Archiwum jest puste. Użyj zakładki 'Indeksuj' aby dodać dokumenty.", ""

    odpowiedz = p.zapytaj_archiwum(pytanie, n_kontekst=3)
    trafienia = p.szukaj(pytanie, n=5)

    zrodla = "\n".join(
        f"• [{t['odleglosc']:.3f}] **{t['plik']}**\n"
        f"  Osoby: {', '.join(t['osoby'][:5]) or '—'}\n"
        f"  Org: {', '.join(t['organizacje'][:5]) or '—'}"
        for t in trafienia
    )
    return odpowiedz, zrodla


def interfejs_indeksuj(folder: str) -> str:
    """Zakładka: Indeksuj folder."""
    sciezka = pathlib.Path(folder.strip())
    if not sciezka.exists():
        return f"Folder nie istnieje: {sciezka}"
    p = zaladuj_pipeline()
    try:
        p.indeksuj_folder(sciezka)
        return f"Zaindeksowano. Dokumentów w bazie: {p.kolekcja.count()}"
    except Exception as e:
        return f"Błąd: {e}"


def interfejs_transkrybuj(plik_audio) -> str:
    """Zakładka: Transkrypcja audio."""
    if plik_audio is None:
        return "Wgraj plik audio."
    from whisper_transkrypcja import transkrybuj
    wynik = transkrybuj(plik_audio, jezyk="pl")
    return wynik["tekst"]


def interfejs_status() -> str:
    """Status systemu."""
    try:
        p = zaladuj_pipeline()
        return f"Dokumentów w bazie: {p.kolekcja.count()}"
    except Exception as e:
        return f"Pipeline nie załadowany ({e}). Kliknij 'Indeksuj' aby go uruchomić."


def interfejs_graf(podmiot: str) -> str:
    """Zakładka: Graf powiązań."""
    from graf_powiazań import buduj_graf, wizualizuj, znajdz_polaczenia
    p = zaladuj_pipeline()
    G = buduj_graf(p.kolekcja)

    if podmiot.strip():
        sciezka = wizualizuj(G, "graf_powiazań.html", filtr_podmiot=podmiot.strip())
        powiazane = znajdz_polaczenia(G, podmiot.strip())
        return f"Graf zapisany: {sciezka}\n\nPowiązane z '{podmiot}':\n" + "\n".join(f"• {x}" for x in powiazane[:20])
    else:
        sciezka = wizualizuj(G, "graf_powiazań.html")
        return f"Graf pełny zapisany: {sciezka}\nWęzłów: {G.number_of_nodes()}, krawędzi: {G.number_of_edges()}"


# ── budowa interfejsu ─────────────────────────────────────────
with gr.Blocks(
    title="AI Dziennikarstwo Śledcze",
    theme=gr.themes.Soft(),
    css=".gradio-container { max-width: 1200px; margin: auto; }",
) as app:

    gr.Markdown("""
    # Archiwum Dziennikarskie AI
    *GTX 1660 SUPER · Bielik 7B · spaCy PL · ChromaDB*
    """)

    with gr.Tab("Przeszukaj archiwum"):
        with gr.Row():
            with gr.Column():
                pytanie_input = gr.Textbox(
                    label="Pytanie",
                    placeholder="np. Kto jest powiązany ze spółką X? Jakie dokumenty dotyczą Jana Kowalskiego?",
                    lines=3,
                )
                szukaj_btn = gr.Button("Zapytaj Bielika", variant="primary")
                status_txt = gr.Textbox(label="Status", value=interfejs_status, interactive=False)

            with gr.Column():
                odpowiedz_out = gr.Textbox(label="Odpowiedź Bielika", lines=10)
                zrodla_out = gr.Markdown(label="Źródła")

        szukaj_btn.click(
            interfejs_szukaj,
            inputs=[pytanie_input],
            outputs=[odpowiedz_out, zrodla_out],
        )

    with gr.Tab("Indeksuj dokumenty"):
        gr.Markdown("Podaj ścieżkę do folderu z dokumentami (PDF, JPG, PNG, TXT).")
        folder_input = gr.Textbox(
            label="Folder z archiwum",
            value="C:/Users/rzecz/AI-Dziennikarstwo/archiwum",
        )
        indeksuj_btn = gr.Button("Indeksuj", variant="primary")
        indeksuj_out = gr.Textbox(label="Wynik")
        indeksuj_btn.click(interfejs_indeksuj, inputs=[folder_input], outputs=[indeksuj_out])

    with gr.Tab("Transkrypcja audio"):
        gr.Markdown("Wgraj nagranie (MP3, MP4, WAV, OGG). Whisper medium, język polski.")
        audio_input = gr.Audio(type="filepath", label="Plik audio/video")
        transkrybuj_btn = gr.Button("Transkrybuj", variant="primary")
        transkrypcja_out = gr.Textbox(label="Transkrypcja", lines=15)
        transkrybuj_btn.click(interfejs_transkrybuj, inputs=[audio_input], outputs=[transkrypcja_out])

    with gr.Tab("Graf powiązań"):
        gr.Markdown("Generuje interaktywny graf powiązań OSINT z zaindeksowanych dokumentów.")
        podmiot_input = gr.Textbox(label="Filtruj po podmiocie (opcjonalnie)", placeholder="np. Jan Kowalski")
        graf_btn = gr.Button("Generuj graf", variant="primary")
        graf_out = gr.Textbox(label="Wynik", lines=10)
        graf_btn.click(interfejs_graf, inputs=[podmiot_input], outputs=[graf_out])

    gr.Markdown("""
    ---
    **Skróty:** `Enter` = wyślij zapytanie · Archiwum: `C:/Users/rzecz/AI-Dziennikarstwo/archiwum/`
    """)


if __name__ == "__main__":
    print("Uruchamiam Web UI na http://localhost:7860")
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
