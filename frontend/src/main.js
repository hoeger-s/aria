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

async function startMicrophone() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

  const audioContext = new AudioContext()
  const source = audioContext.createMediaStreamSource(stream)
  const analyser = audioContext.createAnalyser()
  analyser.fftSize = 256
  source.connect(analyser)

  const data = new Uint8Array(analyser.frequencyBinCount)

  function checkLevel() {
    analyser.getByteFrequencyData(data)
    const average = data.reduce((sum, v) => sum + v, 0) / data.length
    console.log('Mikrofon-Pegel:', average.toFixed(1))
    requestAnimationFrame(checkLevel)
  }
  checkLevel()
}

document.getElementById('start-mic').addEventListener('click', startMicrophone, { once: true })
