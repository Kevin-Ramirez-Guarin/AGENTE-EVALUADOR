import { useId } from 'react'

// Mapa ilustrado (no a escala) con los destinos de Giveaway unidos por una ruta.
// Las posiciones respetan solo la geografía relativa: la costa arriba, los Andes al centro.
const DESTINOS = [
  { nombre: 'Cartagena', x: 112, y: 112, lado: 'izq' },
  { nombre: 'Parque Tayrona', x: 300, y: 84, lado: 'arriba' },
  { nombre: 'Guatapé', x: 228, y: 238, lado: 'der' },
  { nombre: 'Medellín', x: 150, y: 252, lado: 'izq' },
  { nombre: 'Eje Cafetero', x: 132, y: 340, lado: 'izq' },
  { nombre: 'Bogotá', x: 262, y: 336, lado: 'der' },
] as const

const RUTA =
  'M112 112 C170 76 240 66 300 84 C318 150 268 196 228 238 C206 258 176 264 150 252 C112 268 104 312 132 340 C170 376 226 368 262 336'

// Curvas de nivel: anillos irregulares alrededor de dos picos de la cordillera.
function anillo(cx: number, cy: number, r: number, fase: number) {
  const pts = Array.from({ length: 40 }, (_, i) => {
    const t = (i / 40) * Math.PI * 2
    const k = r * (1 + 0.16 * Math.sin(3 * t + fase) + 0.07 * Math.sin(5 * t - fase))
    return `${(cx + k * Math.cos(t)).toFixed(1)} ${(cy + k * 0.82 * Math.sin(t)).toFixed(1)}`
  })
  return `M${pts.join(' L')}Z`
}
const CURVAS = [
  ...[34, 62, 92, 124, 158].map((r, i) => anillo(176, 296, r, i * 0.5)),
  ...[26, 50, 76].map((r, i) => anillo(330, 404, r, 1 + i * 0.4)),
]

export function RutaMapa() {
  const mascara = useId()
  const marco = useId()
  return (
    <svg viewBox="0 0 420 470" className="h-auto w-full" role="img" aria-label="Mapa ilustrado de Colombia con los destinos de Giveaway: Cartagena, Parque Tayrona, Guatapé, Medellín, Eje Cafetero y Bogotá.">
      <defs>
        <clipPath id={marco}>
          <rect width="420" height="470" rx="32" />
        </clipPath>
        <mask id={mascara}>
          <path d={RUTA} pathLength={1} fill="none" stroke="white" strokeWidth={8} strokeDasharray="1 1" className="animate-trazo" />
        </mask>
      </defs>

      <g clipPath={`url(#${marco})`}>
      <rect width="420" height="470" fill="var(--color-selva-800)" />
      <g fill="none" stroke="var(--color-caribe-300)" strokeWidth={1.1} opacity={0.28}>
        {CURVAS.map((d) => <path key={d} d={d} />)}
      </g>

      {/* El mar Caribe al norte */}
      <path d="M0 0H420V58C380 76 350 60 300 70S190 96 130 86 40 104 0 96Z" fill="var(--color-caribe-700)" />
      <g fill="none" stroke="var(--color-caribe-300)" strokeWidth={1.4} strokeLinecap="round" opacity={0.6}>
        <path d="M24 46c10-5 20-5 30 0s20 5 30 0" />
        <path d="M150 30c10-5 20-5 30 0s20 5 30 0" />
        <path d="M270 44c10-5 20-5 30 0s20 5 30 0" />
      </g>
      </g>

      <path d={RUTA} fill="none" stroke="var(--color-mango-300)" strokeWidth={2.6} strokeLinecap="round" strokeDasharray="0.1 8" mask={`url(#${mascara})`} />

      {DESTINOS.map((d) => (
        <g key={d.nombre}>
          <circle cx={d.x} cy={d.y} r={7.5} fill="var(--color-selva-900)" stroke="var(--color-mango-400)" strokeWidth={3} />
          <circle cx={d.x} cy={d.y} r={2.2} fill="var(--color-mango-300)" />
          <text
            x={d.lado === 'der' ? d.x + 15 : d.lado === 'izq' ? d.x - 15 : d.x}
            y={d.lado === 'arriba' ? d.y - 16 : d.y + 5}
            textAnchor={d.lado === 'der' ? 'start' : d.lado === 'izq' ? 'end' : 'middle'}
            fill="white"
            className="font-display text-[15px] font-semibold"
          >
            {d.nombre}
          </text>
        </g>
      ))}
    </svg>
  )
}
