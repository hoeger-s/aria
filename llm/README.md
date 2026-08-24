# LLM-Dienst

Ollama als Docker-Service, stellt das Sprachmodell bereit (vorläufig Qwen2.5 7B).

## Status

Getestet (24.08.2026): Ollama-Container mit GPU-Zugriff, Modell `qwen2.5:7b` heruntergeladen,
per Testanfrage erfolgreich geprüft. Läuft gemeinsam mit den anderen beiden Diensten über `docker compose up -d`, siehe `docker-compose.yml`.

**Beispiel-Anfrage und Antwort:**

```powershell
$body = @{
    model   = "qwen2.5:7b"
    prompt  = "Was ist die Hauptstadt von Deutschland, und seit wann ist das so?"
    stream  = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
```

```powershell
model                : qwen2.5:7b
created_at           : 2026-08-24T08:37:36.448735043Z
response             : Die Hauptstadt von Deutschland ist Berlin. Dies ist seit dem 7. Oktober 1990, dem Wiedervereinigungsday, der Fall.
                       Vor dieser Zeit war Bonn die deutscher Hauptstadt, da West-Berlin während des Kalten Krieges nicht als Hauptstadt
                       anerkannt wurde.
done                 : True
done_reason          : stop
context              : {151644, 8948, 198, 2610...}
total_duration       : 623686043
load_duration        : 5660804
prompt_eval_count    : 44
prompt_eval_duration : 20995000
eval_count           : 70
eval_duration        : 592134000
```
