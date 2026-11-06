import { useId, type ReactNode, type SVGProps } from 'react'
import type { EstadoEvaluacion, Veredicto } from './api'
import { ESTADOS, VEREDICTOS } from './estados'

export function Insignia({ clase, punto, forma = 'rounded-full', children }: { clase: string; punto?: string; forma?: string; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap ${forma} px-2.5 py-0.5 text-sm font-medium ring-1 ring-inset ${clase}`}>
      {punto && <span aria-hidden="true" className={`size-1.5 rounded-full ${punto}`} />}
      {children}
    </span>
  )
}

// Un estado desconocido se muestra tal cual, en gris.
export const EstadoInsignia = ({ estado }: { estado: EstadoEvaluacion }) => {
  const e = ESTADOS[estado] ?? { texto: estado, clase: 'bg-niebla-100 text-niebla-900 ring-niebla-300', punto: 'bg-niebla-500' }
  return <Insignia clase={e.clase} punto={e.punto}>{e.texto}</Insignia>
}

export const VeredictoInsignia = ({ veredicto }: { veredicto: Veredicto }) => {
  const v = VEREDICTOS[veredicto] ?? { texto: veredicto, clase: 'bg-niebla-100 text-niebla-900 ring-niebla-300' }
  return <Insignia clase={v.clase} forma="rounded-md">{v.texto}</Insignia>
}

export function Campo({ id, label, error, ayuda, children }: { id: string; label: string; error?: string; ayuda?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="font-semibold text-niebla-900">{label}</label>
      {ayuda && <p id={`${id}-ayuda`} className="mt-0.5 text-sm text-niebla-600">{ayuda}</p>}
      {children}
      {error && (
        <p id={`${id}-error`} className="mt-1.5 flex items-start gap-1.5 text-sm font-medium text-red-700">
          <IconoAlerta className="mt-0.5 size-4 shrink-0" />
          {error}
        </p>
      )}
    </div>
  )
}

// Banda oscura con el h1 de las páginas internas del sitio de empleo; continúa el encabezado.
export function BandaTitulo({ titulo, antes, children, className = 'pb-12' }: { titulo: string; antes?: ReactNode; children?: ReactNode; className?: string }) {
  return (
    <div data-tono="oscuro" className="bg-selva-900 text-white">
      <div className={`mx-auto max-w-6xl space-y-4 px-4 pt-6 sm:px-6 ${className}`}>
        {antes}
        <h1 className="max-w-3xl text-titulo font-semibold">{titulo}</h1>
        {children}
      </div>
    </div>
  )
}

// Iconos de trazo (24×24), decorativos: el texto vecino da el significado.
function Icono({ children, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}>
      {children}
    </svg>
  )
}
export const IconoAlerta = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><circle cx="12" cy="12" r="9" /><path d="M12 7.5v5.5M12 16.5v.01" /></Icono>
export const IconoCheck = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="m5 12.5 4.5 4.5L19 7.5" /></Icono>
export const IconoMenos = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="M6 12h12" /></Icono>
export const IconoVolver = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="M15 18l-6-6 6-6" /></Icono>
export const IconoRefrescar = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="M20 11a8 8 0 0 0-14.3-4.9L4 8M4 4v4h4M4 13a8 8 0 0 0 14.3 4.9L20 16M20 20v-4h-4" /></Icono>
export const IconoUbicacion = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z" /><circle cx="12" cy="10" r="2.3" /></Icono>
export const IconoEquipo = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><circle cx="9" cy="8.5" r="3" /><path d="M3.5 19a5.5 5.5 0 0 1 11 0M16 5.8a3 3 0 0 1 0 5.4M17.5 14.2A5.5 5.5 0 0 1 20.5 19" /></Icono>
export const IconoModalidad = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><rect x="3.5" y="5" width="17" height="11" rx="1.5" /><path d="M8.5 20h7M12 16v4" /></Icono>
export const IconoDocumento = (p: SVGProps<SVGSVGElement>) => <Icono {...p}><path d="M14 3.5H7.5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8z" /><path d="M14 3.5V8h4.5M9 13h6M9 16.5h4" /></Icono>

// Marca de Giveaway: un pin de mapa con sol, montaña y mar.
export function Marca({ className = 'h-9 w-auto' }: { className?: string }) {
  const id = useId()
  return (
    <svg viewBox="0 0 32 40" className={className} aria-hidden="true" focusable="false">
      <defs>
        <clipPath id={id}>
          <path d="M16 1C7.7 1 1.5 7.3 1.5 15.3 1.5 25.6 16 39 16 39s14.5-13.4 14.5-23.7C30.5 7.3 24.3 1 16 1z" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${id})`}>
        <rect width="32" height="40" fill="var(--color-selva-800)" />
        <circle cx="20.5" cy="12" r="5" fill="var(--color-mango-400)" />
        <path d="M0 26 9 14.5l5 6 4-4.5L32 27v13H0z" fill="var(--color-caribe-500)" />
        <path d="M0 27.5c2.7-1.6 5.3-1.6 8 0s5.3 1.6 8 0 5.3-1.6 8 0 5.3 1.6 8 0V40H0z" fill="var(--color-caribe-300)" />
      </g>
    </svg>
  )
}

export function Logo({ tono = 'oscuro' }: { tono?: 'oscuro' | 'claro' }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Marca />
      <span className={`font-display text-2xl font-bold tracking-[-0.03em] ${tono === 'oscuro' ? 'text-white' : 'text-selva-900'}`}>giveaway</span>
    </span>
  )
}
