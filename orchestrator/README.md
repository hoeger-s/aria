# Orchestrator

FastAPI-Backend, verbindet STT-, LLM- und TTS-Dienst zu einer durchgehenden Pipeline: Audio oder Text rein, gesprochene Antwort raus.

## Status

**Aktive Schnittstelle: `/ws` (WebSocket)** Genutzt vom Frontend seit 05.09.2026.
Nimmt Text (JSON-Frame) oder Audio (Binär-Frame) entgegen, der Frame-Typ selbst dient als Typ-Marker. Antwort läuft komplett gestreamt: LLM-Tokens gehen live raus (`{"type": "token", ...}`), parallel dazu werden fertige Sätze einzeln vertont und als eigene Binär-Frames verschickt, sobald sie fertig sind (kein Warten auf die komplette Antwort). Ein `{"type": "response_complete"}` markiert das Ende. Nebenläufig über ein Produzent-/Konsument-Muster (`asyncio.Queue`) umgesetzt, damit Text-Streaming nicht durch die TTS-Wartezeit blockiert wird.

**Ältere Schnittstelle: `/converse` (HTTP, weiterhin vorhanden)** Nimmt Audio oder Text per Formular entgegen, liefert die komplette Antwort als eine WAV-Datei zurück (nicht gestreamt). Für schnelle manuelle Tests per `curl` weiterhin praktisch, vom Frontend aber nicht mehr genutzt.

Läuft lokal über `uvicorn`, noch nicht Teil von `docker-compose.yml`. Bewusst zurückgestellt solange aktiv am Frontend weitergearbeitet wird.

**Beispiel-Anfrage über `/converse` (Text-Eingabe):**

```powershell
curl.exe -X POST http://localhost:8000/converse -F "text=Erklaere in drei kurzen Saetzen, wie Fotosynthese funktioniert." -o example.wav
```

**Beispiel-Anfrage über `/converse` (Audio-Eingabe):**

```powershell
curl.exe -X POST http://localhost:8000/converse -F "file=@Aufzeichnung.m4a" -o antwort.wav
```
