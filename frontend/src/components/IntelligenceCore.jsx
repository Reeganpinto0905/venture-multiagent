import { useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Float, Sparkles } from '@react-three/drei'

const ACCENT = '#6ee7b7'
const ACCENT_DIM = '#1f4a3a'
const DIM = '#233330'

const STATE_CONFIG = {
  idle: { spin: 0.06, sparkles: 60, pulse: 0.15, ringSpeed: 0.1 },
  thinking: { spin: 0.16, sparkles: 90, pulse: 0.35, ringSpeed: 0.22 },
  question: { spin: 0.1, sparkles: 75, pulse: 0.5, ringSpeed: 0.16 },
  retrieving: { spin: 0.24, sparkles: 120, pulse: 0.45, ringSpeed: 0.3 },
  analyzing: { spin: 0.32, sparkles: 140, pulse: 0.6, ringSpeed: 0.42 },
  complete: { spin: 0.05, sparkles: 40, pulse: 0.2, ringSpeed: 0.08 },
}

function Satellite({ radius, tilt, axis, speed, offset }) {
  const ref = useRef()

  useFrame(() => {
    if (!ref.current) return
    const t = (performance.now() * 0.001) * speed + offset
    const x = Math.cos(t) * radius
    const z = Math.sin(t) * radius
    const v = new THREE.Vector3(x, 0, z).applyAxisAngle(axis, tilt)
    ref.current.position.copy(v)
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.05, 12, 12]} />
      <meshStandardMaterial color={ACCENT} emissive={ACCENT} emissiveIntensity={1.4} />
    </mesh>
  )
}

function OrbitRing({ radius, tilt, axis, spin, satelliteSpeed, satelliteOffset }) {
  const ref = useRef()

  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.z += delta * spin
  })

  return (
    <group>
      <group ref={ref} quaternion={new THREE.Quaternion().setFromAxisAngle(axis, tilt)}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[radius, 0.004, 8, 96]} />
          <meshBasicMaterial color={DIM} transparent opacity={0.7} />
        </mesh>
      </group>
      <Satellite radius={radius} tilt={tilt} axis={axis} speed={satelliteSpeed} offset={satelliteOffset} />
    </group>
  )
}

function GlowSprite({ scale = 3.4, color = 'rgba(110, 231, 183,' }) {
  const texture = useMemo(() => {
    const size = 256
    const canvas = document.createElement('canvas')
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2)
    gradient.addColorStop(0, `${color} 0.55)`)
    gradient.addColorStop(0.45, `${color} 0.16)`)
    gradient.addColorStop(1, `${color} 0)`)
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, size, size)
    return new THREE.CanvasTexture(canvas)
  }, [color])

  useEffect(() => {
    return () => {
      if (texture) texture.dispose()
    }
  }, [texture])

  return (
    <sprite scale={[scale, scale, 1]}>
      <spriteMaterial map={texture} transparent depthWrite={false} />
    </sprite>
  )
}

function Core({ phase }) {
  const groupRef = useRef()
  const rigRef = useRef()
  const sphereRef = useRef()
  const wireRef = useRef()
  const { pointer } = useThree()
  const config = STATE_CONFIG[phase] || STATE_CONFIG.idle

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * config.spin
    }
    if (wireRef.current) {
      wireRef.current.rotation.y -= delta * config.spin * 0.6
      wireRef.current.rotation.x += delta * config.spin * 0.2
    }
    if (sphereRef.current) {
      const base = 1
      const pulse = base + Math.sin(Date.now() * 0.0015) * config.pulse * 0.06
      sphereRef.current.scale.setScalar(pulse)
    }
    if (rigRef.current) {
      const targetX = pointer.y * 0.22
      const targetY = pointer.x * 0.26
      rigRef.current.rotation.x += (targetX - rigRef.current.rotation.x) * 0.03
      rigRef.current.rotation.y += (targetY - rigRef.current.rotation.y) * 0.03
    }
  })

  const rings = useMemo(
    () => [
      { radius: 1.5, tilt: 0.35, axis: new THREE.Vector3(1, 0.2, 0), satelliteOffset: 0 },
      { radius: 1.9, tilt: -0.55, axis: new THREE.Vector3(0.3, 1, 0), satelliteOffset: 2.1 },
      { radius: 2.25, tilt: 0.9, axis: new THREE.Vector3(0, 0.4, 1), satelliteOffset: 4.2 },
    ],
    []
  )

  return (
    <group ref={rigRef}>
      <ambientLight intensity={0.4} />
      <pointLight position={[3, 3, 4]} intensity={1.2} color={ACCENT} />
      <pointLight position={[-3, -2, -3]} intensity={0.5} color={ACCENT_DIM} />

      <group ref={groupRef}>
        <GlowSprite />

        <mesh ref={sphereRef}>
          <icosahedronGeometry args={[0.72, 3]} />
          <meshStandardMaterial
            color="#0b0f0e"
            emissive={ACCENT}
            emissiveIntensity={0.55}
            roughness={0.25}
            metalness={0.6}
          />
        </mesh>

        <mesh ref={wireRef}>
          <icosahedronGeometry args={[0.95, 1]} />
          <meshBasicMaterial color={ACCENT} wireframe transparent opacity={0.22} />
        </mesh>
      </group>

      {rings.map((ring, i) => (
        <OrbitRing
          key={i}
          radius={ring.radius}
          tilt={ring.tilt}
          axis={ring.axis}
          spin={config.ringSpeed * (i % 2 === 0 ? 1 : -1)}
          satelliteSpeed={0.4 + i * 0.15}
          satelliteOffset={ring.satelliteOffset}
        />
      ))}

      <Float speed={1.4} rotationIntensity={0.15} floatIntensity={0.4}>
        <Sparkles
          count={config.sparkles}
          scale={[5, 5, 5]}
          size={2.2}
          speed={0.25}
          color={ACCENT}
          opacity={0.55}
        />
      </Float>
    </group>
  )
}

export default function IntelligenceCore({ phase = 'idle', className = '' }) {
  return (
    <div className={className} aria-hidden="true" style={{ pointerEvents: 'none' }}>
      <Canvas
        camera={{ position: [0, 0, 4.6], fov: 40 }}
        gl={{ alpha: true, antialias: true, powerPreference: 'high-performance' }}
        dpr={[1, 2]}
      >
        <Core phase={phase} />
      </Canvas>
    </div>
  )
}