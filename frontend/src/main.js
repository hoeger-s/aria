import './style.css'
import * as THREE from 'three'

// Szene: der "Raum", in dem alle 3D-Objekte existieren
const scene = new THREE.Scene()
scene.background = new THREE.Color(0x05050a)

// Kamera: bestimmt, aus welcher Perspektive wir die Szene sehen
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100)
camera.position.z = 5

// Renderer: zeichnet die Szene tatsächlich als Bild und hängt sie ins HTML
const renderer = new THREE.WebGLRenderer({ antialias: true})
renderer.setSize(window.innerWidth, window.innerHeight)
renderer.setPixelRatio(window.devicePixelRatio)
document.getElementById('app').appendChild(renderer.domElement)

// Orb-Platzhalter: eine Kugel, Farbe = Idle-Zustand (gedimmtes Blau/Grau)
const geometry = new THREE.SphereGeometry(1, 32, 32)
const material = new THREE.MeshStandardMaterial({
  color: 0x3a4a5c,
  roughness: 0.4,   // 0 = spiegelglatt, 1 = komplett matt
  metalness: 0.2,   // leichter metallischer Glanz statt Kunststoff-Look
})
const orb = new THREE.Mesh(geometry, material)
scene.add(orb)

// Punktlicht, wirft einen Glanzpunkt/Schatten-Verlauf auf die Kugel
const pointLight = new THREE.PointLight(0xffffff, 100)
pointLight.position.set(3, 3, 3)
scene.add(pointLight)

// Umgebungslicht, damit die Schattenseite nicht komplett schwarz absäuft
scene.add(new THREE.AmbientLight(0xffffff, 0.5))

// Render-Loop: zeichnet die Szene immer wieder neu (nötig für spätere Animation)
function animate() {
  requestAnimationFrame(animate)
  renderer.render(scene, camera)
}
animate()

// Sorgt dafür, dass die Szene bei Fenstergröße-Änderung mitwächst
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight)
})

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

  function checkLevel() {
    analyser.getByteFrequencyData(data)
    const average = data.reduce((sum, v) => sum + v, 0) / data.length
    const now = performance.now()

    if (average > SPEECH_THRESHOLD) {
      belowThresholdSince = null
      if (aboveThresholdSince === null) aboveThresholdSince = now
      if (!isSpeaking && now - aboveThresholdSince > START_DELAY_MS) {
        isSpeaking = true
        console.log('%cSprechbeginn erkannt', 'color: lightgreen')
      }
    } else {
      aboveThresholdSince = null
      if (belowThresholdSince === null) belowThresholdSince = now
      if (isSpeaking && now - belowThresholdSince > END_DELAY_MS) {
        isSpeaking = false
        console.log('%cSprechende erkannt', 'color: orange')
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
    startMicrophone()
  } else {
    modeToggleButton.textContent = '🎤'
    textInputContainer.style.display = 'block'
    stopMicrophone()
    textInput.focus()
  }
}

modeToggleButton.addEventListener('click', () => {
  setMode(mode === 'voice' ? 'text' : 'voice')
})

// Falls der Browser den Audio-Kontext wegen der Autoplay-Policy zunaechst
// "suspended" laesst (kein Klick vor dem automatischen Start passiert):
// beim ersten Klick irgendwo auf der Seite reaktivieren.
document.addEventListener('click', () => {
  if (audioContext && audioContext.state === 'suspended') {
    audioContext.resume()
  }
})

setMode('voice')
