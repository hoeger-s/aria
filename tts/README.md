# TTS-Dienst

Sprachausgabe über faster-qwen3-tts (CUDA-Graph-optimiert), Docker-Container mit CUDA-Basis-Image.
Wandelt Text in gesprochenes Audio um (1.7B-Modell, Preset-Stimme).

## Status

Getestet (24.08.2026): Eigenes Docker-Image gebaut (CUDA-Basis-Image), Container mit GPU-Zugriff gestartet,
per echtem Testsatz erfolgreich geprüft. Verständliche deutsche Sprachausgabe (mit englischem Akzent, keine
native deutsche Preset-Stimme verfügbar), ca. 1,29s bei warmem Modell.
Läuft gemeinsam mit den anderen beiden Diensten über `docker compose up -d`, siehe `docker-compose.yml`.

> Beispiel-Audio: [example.wav](example.wav)

**Beispiel-Anfrage:**

```powershell
$body = @{
    text        = "Hallo, ich bin ARIA. Das ist ein Test der Sprachausgabe."
    speaker     = "aiden"
    language    = "German"
} | ConvertTo-Json
```

```powershell
Measure-Command {
    Invoke-RestMethod -Uri "http://localhost:8002/speak" -Method Post -Body $body -ContentType "application/json" -OutFile "example.wav"
}
```

```powershell
Days              : 0
Hours             : 0
Minutes           : 0
Seconds           : 1
Milliseconds      : 291
Ticks             : 12911780
TotalDays         : 1,49441898148148E-05
TotalHours        : 0,000358660555555556
TotalMinutes      : 0,0215196333333333
TotalSeconds      : 1,291178
TotalMilliseconds : 1291,178
```
