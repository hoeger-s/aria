import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import sounddevice as sd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BLOCK_DURATION = 0.1  # Sekunden pro Haeppchen, wie im Mikrofon-Test
SPIKE_THRESHOLD = (
    0.02  # ab hier zaehlt ein Block als "laut" - liegt zwischen Grundrauschen und Klatsch-Pegel
)
MAX_SPIKE_BLOCKS = 2  # laenger als 200ms am Stueck laut = Dauergeraeusch/Sprache, kein Klatschen
DOUBLE_CLAP_WINDOW = (0.15, 0.8)  # Sekunden zwischen zwei gueltigen Klatschern

recent_claps = deque(maxlen=2)
above_threshold_count = 0
triggered = False


def trigger_start_script():
    global triggered
    print("Doppelklatschen erkannt - starte ARIA...")
    subprocess.Popen(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PROJECT_ROOT / "scripts" / "start.ps1"),
        ],
        cwd=str(PROJECT_ROOT),
    )
    triggered = True  # ARIA wird gestartet - Skript hoert danach auf zu lauschen


def process_block(indata, frames, time_info, status):
    global above_threshold_count

    if triggered:
        return  # nichts mehr tun, wir warten nur noch aufs Beenden

    if status:
        print(status)

    level = np.sqrt(np.mean(indata**2))
    now = time.monotonic()

    if level > SPIKE_THRESHOLD:
        above_threshold_count += 1
    else:
        if 0 < above_threshold_count <= MAX_SPIKE_BLOCKS:
            recent_claps.append(now)
            if len(recent_claps) == 2:
                gap = recent_claps[1] - recent_claps[0]
                if DOUBLE_CLAP_WINDOW[0] <= gap <= DOUBLE_CLAP_WINDOW[1]:
                    trigger_start_script()
                    recent_claps.clear()
        above_threshold_count = 0


with sd.InputStream(
    callback=process_block, channels=1, samplerate=16000, blocksize=int(16000 * BLOCK_DURATION)
):
    print("Warte auf Doppelklatschen (Strg+C zum Beenden)...")
    while not triggered:
        sd.sleep(1000)

print("ARIA wird gestartet, Wakeword-Skript beendet sich.")
sys.exit(0)
