# STT-Dienst

Spracherkennung über faster-whisper, Docker-Container mit CUDA-Basis-Image. Wandelt Sprache in Text um (Modellgröße "small").

## Status

Getestet (24.08.2026): Eigenes Docker-Image gebaut (CUDA-Basis-Image), Container mit GPU-Zugriff gestartet,
per echter Sprachaufnahme erfolgreich geprüft. Läuft aktuell über einzelne Docker-Befehle, noch nicht
in eine `docker-compose.yml` überführt.

**Beispiel-Anfrage und Antwort:**

```powershell
curl.exe -X POST http://localhost:8001/transcribe -F "file=@C:\Users\stefa\Documents\Audioaufzeichnungen\Aufzeichnung.m4a"
```

```powershell
{"text":"Hallo, das ist ein Test für ARIA.","language":"de"}
```
