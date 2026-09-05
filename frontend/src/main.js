import './style.css'
import * as THREE from 'three'

// Szene: der "Raum", in dem alle 3D-Objekte existieren
const scene = new THREE.Scene()
scene.background = new THREE.Color(0x05050a)

// Kamera: bestimmt, aus welcher Perspektive wir die Szene sehen
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100)
camera.position.z = 5

// Renderer: zeichnet die Szene tatsächlich als Bild und hängt sie ins HTML
const renderer = new THREE.WebGLRenderer({ antialias: true })
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
document.getElementById('app').appendChild(renderer.domElement)

// Orb: eine Kugel, Grundfarbe + zustandsabhaengiges Gluehen (emissive) obendrauf
const geometry = new THREE.SphereGeometry(1, 32, 32)
const material = new THREE.MeshStandardMaterial({
  color: 0x3a4a5c,
  roughness: 0.4,
  metalness: 0.2,
  emissive: 0x000000,
})
const orb = new THREE.Mesh(geometry, material)
orb.position.y = 0.8
scene.add(orb)

// Punktlicht, wirft einen Glanzpunkt/Schatten-Verlauf auf die Kugel
const pointLight = new THREE.PointLight(0xffffff, 100)
pointLight.position.set(3, 3, 3)
scene.add(pointLight)

// Umgebungslicht, damit die Schattenseite nicht komplett schwarz absäuft
scene.add(new THREE.AmbientLight(0xffffff, 0.5))

// Zustandsfarben laut Architektur-Notiz (UI-Layout und Farbschema)
const STATE_COLORS = {
  idle: new THREE.Color(0x3a4a5c),       // gleiche Farbe wie die Kugel selbst, nur als Glimmen
  listening: new THREE.Color(0x3a4a5c),  // identisch zu idle
  thinking: new THREE.Color(0x8b5cf6),   // sanftes Violett
  speaking: new THREE.Color(0xd7f5ff),   // helles Cyan/Weiss
}

let orbState = 'idle'
let orbLevel = 0        // roher Pegel-Wert aus der Analyse (Mikrofon bei listening, Wiedergabe bei speaking)
let orbDisplayLevel = 0 // geglaetteter Wert, den die Optik tatsaechlich nutzt - verhindert hektisches Zucken

function updateOrbAppearance() {
  material.emissive.lerp(STATE_COLORS[orbState], 0.05)
  orbDisplayLevel += (orbLevel - orbDisplayLevel) * 0.15

  let targetScale = 1

  if (orbState === 'thinking') {
    const thinkPhase = Math.sin(performance.now() / 300)
    material.emissiveIntensity = 0.5 + thinkPhase * 0.3
    targetScale = 1 + thinkPhase * 0.05
  } else if (orbState === 'speaking') {
    material.emissiveIntensity = 0.1 + orbDisplayLevel * 0.6
    targetScale = 1 + orbDisplayLevel * 0.15
  } else {
    const breathePhase = Math.sin(performance.now() / 1000)
    material.emissiveIntensity = Math.max(breathePhase, 0) * 0.4
    targetScale = 1 + breathePhase * 0.03
  }

  const currentScale = orb.scale.x
  const newScale = currentScale + (targetScale - currentScale) * 0.05
  orb.scale.setScalar(newScale)
}

// Render-Loop: zeichnet die Szene immer wieder neu, aktualisiert dabei den Orb-Zustand
function animate() {
  requestAnimationFrame(animate)
  updateOrbAppearance()
  renderer.render(scene, camera)
}
animate()

// Sorgt dafür, dass die Szene bei Fenstergröße-Änderung mitwächst
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
})

const chatLog = document.getElementById('chat-log')
let currentAssistantMessageEl = null

function addUserMessage(text) {
  const el = document.createElement('div')
  el.className = 'chat-message chat-message-user'
  el.textContent = text
  chatLog.appendChild(el)
  currentAssistantMessageEl = null
  chatLog.scrollTop = chatLog.scrollHeight
}

function appendAssistantToken(token) {
  if (!currentAssistantMessageEl) {
    currentAssistantMessageEl = document.createElement('div')
    currentAssistantMessageEl.className = 'chat-message chat-message-assistant'
    chatLog.appendChild(currentAssistantMessageEl)
  }
  currentAssistantMessageEl.textContent += token
  chatLog.scrollTop = chatLog.scrollHeight
}

const SPEECH_THRESHOLD = 15
const START_DELAY_MS = 100
const END_DELAY_MS = 500

let mode = 'voice'
let micStream = null
let audioContext = null
let animationFrameId = null

const modeToggleButton = document.getElementById('mode-toggle')
const textInputContainer = document.getElementById('text-input-container')
const textInput = document.getElementById('text-input')

// Eigener AudioContext nur fuers Abspielen der TTS-Antworten - unabhaengig vom
// Mikrofon-AudioContext, der beim Wechsel in den Textmodus komplett geschlossen wird
const playbackContext = new AudioContext()

// WebSocket-Verbindung zum Orchestrator
const ws = new WebSocket('ws://localhost:8000/ws')

ws.addEventListener('open', () => {
  console.log('%cWebSocket verbunden', 'color: lightgreen')
})

ws.addEventListener('close', () => {
  console.log('%cWebSocket getrennt', 'color: orange')
})

ws.addEventListener('error', (event) => {
  console.error('WebSocket-Fehler', event)
})

ws.addEventListener('message', (event) => {
  if (typeof event.data === 'string') {
    const payload = JSON.parse(event.data)
    if (payload.type === 'user_message') {
      addUserMessage(payload.content)
    } else if (payload.type === 'token') {
      console.log('%c' + payload.content, 'color: cyan')
      appendAssistantToken(payload.content)
    }
  } else {
    console.log('Audio-Antwort erhalten:', event.data.size, 'Bytes')
    playAudioResponse(event.data)
  }
})

async function playAudioResponse(blob) {
  if (blob.size === 0) {
    console.warn('Leere Audio-Antwort erhalten (z. B. weil nichts Verstaendliches erkannt wurde) - nichts abzuspielen')
    orbState = mode === 'voice' ? 'listening' : 'idle'
    return
  }

  const arrayBuffer = await blob.arrayBuffer()
  const audioBuffer = await playbackContext.decodeAudioData(arrayBuffer)

  const source = playbackContext.createBufferSource()
  source.buffer = audioBuffer

  const gainNode = playbackContext.createGain()
  gainNode.gain.value = 0.5 // Lautstaerke der Wiedergabe - senkt gleichzeitig den analysierten Pegel

  const playbackAnalyser = playbackContext.createAnalyser()
  playbackAnalyser.fftSize = 256
  const playbackData = new Uint8Array(playbackAnalyser.frequencyBinCount)

  source.connect(gainNode)
  gainNode.connect(playbackAnalyser)
  playbackAnalyser.connect(playbackContext.destination)

  function updatePlaybackLevel() {
    if (orbState !== 'speaking') return
    playbackAnalyser.getByteFrequencyData(playbackData)
    const average = playbackData.reduce((sum, v) => sum + v, 0) / playbackData.length
    orbLevel = Math.min(average / 50, 1)
    requestAnimationFrame(updatePlaybackLevel)
  }

  source.onended = () => {
    orbState = mode === 'voice' ? 'listening' : 'idle'
    orbLevel = 0
  }

  orbState = 'speaking'
  source.start()
  updatePlaybackLevel()
}

function sendAudio(blob) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(blob)
    orbLevel = 0
    orbDisplayLevel = 0
    orbState = 'thinking'
  }
}

function sendText(text) {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text }))
    orbLevel = 0
    orbDisplayLevel = 0
    orbState = 'thinking'
  }
}

textInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && textInput.value.trim() !== '') {
    sendText(textInput.value.trim())
    textInput.value = ''
  }
})

async function startMicrophone() {
  micStream = await navigator.mediaDevices.getUserMedia({ audio: true })

  audioContext = new AudioContext()
  const source = audioContext.createMediaStreamSource(micStream)
  const analyser = audioContext.createAnalyser()
  analyser.fftSize = 256
  source.connect(analyser)

  const data = new Uint8Array(analyser.frequencyBinCount)

  let isSpeaking = false
  let aboveThresholdSince = null
  let belowThresholdSince = null
  let recorder = null
  let recordedChunks = []

  function startRecording() {
    recordedChunks = []
    recorder = new MediaRecorder(micStream)
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) recordedChunks.push(event.data)
    }
    recorder.start()
  }

  function stopRecordingAndSend() {
    if (!recorder) return
    recorder.onstop = () => {
      const audioBlob = new Blob(recordedChunks, { type: recorder.mimeType })
      sendAudio(audioBlob)
    }
    recorder.stop()
  }

  function checkLevel() {
    analyser.getByteFrequencyData(data)
    const average = data.reduce((sum, v) => sum + v, 0) / data.length
    const now = performance.now()

    if (orbState === 'listening') {
      orbLevel = Math.min(average / 50, 1)
    }

    if (average > SPEECH_THRESHOLD) {
      belowThresholdSince = null
      if (aboveThresholdSince === null) aboveThresholdSince = now
      if (!isSpeaking && now - aboveThresholdSince > START_DELAY_MS) {
        isSpeaking = true
        console.log('%cSprechbeginn erkannt', 'color: lightgreen')
        startRecording()
      }
    } else {
      aboveThresholdSince = null
      if (belowThresholdSince === null) belowThresholdSince = now
      if (isSpeaking && now - belowThresholdSince > END_DELAY_MS) {
        isSpeaking = false
        console.log('%cSprechende erkannt', 'color: orange')
        stopRecordingAndSend()
      }
    }

    animationFrameId = requestAnimationFrame(checkLevel)
  }
  checkLevel()
}

function stopMicrophone() {
  if (animationFrameId !== null) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop())
    micStream = null
  }
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
}

function setMode(newMode) {
  mode = newMode

  if (mode === 'voice') {
    modeToggleButton.textContent = '⌨'
    textInputContainer.style.display = 'none'
    orbState = 'listening'
    startMicrophone()
  } else {
    modeToggleButton.textContent = '🎤'
    textInputContainer.style.display = 'block'
    orbState = 'idle'
    stopMicrophone()
    textInput.focus()
  }
}

modeToggleButton.addEventListener('click', () => {
  setMode(mode === 'voice' ? 'text' : 'voice')
})

// Falls der Browser Audio-Kontexte wegen der Autoplay-Policy zunaechst
// "suspended" laesst (kein Klick vor dem automatischen Start passiert):
// beim ersten Klick irgendwo auf der Seite reaktivieren.
document.addEventListener('click', () => {
  if (audioContext && audioContext.state === 'suspended') {
    audioContext.resume()
  }
  if (playbackContext.state === 'suspended') {
    playbackContext.resume()
  }
})

setMode('voice')
