# Frontend

Web-Stack mit Three.js, Orb-UI als Platzhalter statt vollem 3D-Avatar (Phase 1). Sprach- und Textmodus, WebSocket-Verbindung zum Orchestrator, Live-Chatfenster.

## Status

Getestet (05.09.2026): Three.js-Grundgerüst mit Orb, kontinuierliches Mikrofon-Zuhören mit Voice Activity Detection (Schwellenwert + Hysterese), Sprach-/Textmodus-Umschalter, WebSocket-Verbindung zum Orchestrator (der WebSocket-Frame-Typ selbst dient als Typ-Marker: Binär = Audio, Text = JSON), Audio-Wiedergabe mit reaktivem Orb-Zustandsmodell (Idle/Listening/Thinking/Speaking), Live-Chatfenster mit Text- und Sprechblasen. Text und Audio laufen jeweils satzweise gestreamt statt am Ende gesammelt.

**Lokal starten** (Node.js benötigt, `npm install` einmalig vorher im `frontend/`-Ordner):

```powershell
cd frontend
npm run dev
```

Läuft dann unter `http://localhost:5173`, verbindet sich mit dem Orchestrator unter `ws://localhost:8000/ws` (dieser muss vorher separat gestartet sein. Siehe orchestrator/README.md)
