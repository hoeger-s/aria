# Orchestrator

FastAPI-Backend, verbindet STT-, LLM- und TTS-Dienst zu einer durchgehenden Pipeline: Audio oder Text rein, gesprochene Antwort raus.

## Status

Getestet (28.08.2026): Health-Endpoint, asynchrone Verbindungslogik zu allen drei Diensten (httpx, geteilter Client über FastAPI-`lifespan`), Audio- und
Text-Eingabe über einen gemeinsamen `/converse`-Endpunkt. Antwort wird an Satzgrenzen gechunkt und nebenläufig an TTS geschickt statt die komplette Antwort abzuwarten.
Roher Token-Stream zusätzlich für die spätere Live-Textanzeige verfügbar. Läuft lokal über `uvicorn`, noch nicht Teil von `docker-compose.yml`.

**Beispiel-Anfrage (Text-Eingabe):**

```powershell
curl.exe -X POST http://localhost:8000/converse -F "text=Erklaere in drei kurzen Saetzen, wie Fotosynthese funktioniert." -o example.wav
```

**Beispiel-Anfrage (Audio-Eingabe):**

```powershell
curl.exe -X POST http://localhost:8000/converse -F "file=@Aufzeichnung.m4a" -o antwort.wav
```
