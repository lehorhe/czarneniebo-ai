@echo off
echo Aktywowanie venv ai-pipeline...
call C:\Users\rzecz\ai-pipeline\Scripts\activate.bat

echo.
echo Wybierz co uruchomić:
echo 1. Web UI (interfejs dla dziennikarzy)    - http://localhost:7860
echo 2. File Watcher (auto-indeksowanie)
echo 3. JupyterLab (środowisko deweloperskie)
echo 4. Test pipeline (szybki test systemu)
echo.

set /p WYBOR="Wpisz 1, 2, 3 lub 4: "

if "%WYBOR%"=="1" (
    echo Uruchamiam Web UI...
    cd C:\Users\rzecz\AI-Dziennikarstwo
    python -m czarneniebo.web_ui
)
if "%WYBOR%"=="2" (
    echo Uruchamiam File Watcher...
    cd C:\Users\rzecz\AI-Dziennikarstwo
    python -m czarneniebo.file_watcher
)
if "%WYBOR%"=="3" (
    echo Uruchamiam JupyterLab...
    cd C:\Users\rzecz\AI-Dziennikarstwo
    jupyter lab
)
if "%WYBOR%"=="4" (
    echo Test systemu...
    python -c "
import torch
print('GPU:', torch.cuda.get_device_name(0))
import spacy
nlp = spacy.load('pl_core_news_lg')
doc = nlp('Jan Kowalski zarządza spółką Orlen w Warszawie.')
print('NER:', [(e.text, e.label_) for e in doc.ents])
import chromadb
c = chromadb.PersistentClient(path='C:/Users/rzecz/AI-Dziennikarstwo/archiwum_db')
coll = c.get_or_create_collection('archiwum_dziennikarskie')
print('Dokumenty w ChromaDB:', coll.count())
print()
print('Wszystko działa!')
"
    pause
)
