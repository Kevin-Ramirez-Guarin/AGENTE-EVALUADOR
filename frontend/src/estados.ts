import { useEffect } from 'react'
import type { EstadoEvaluacion, Veredicto } from './api'

export const REFRESCO_MS = 5000

// `punto` es el indicador de color junto al texto; el texto siempre acompaña al color.
export const ESTADOS: Record<EstadoEvaluacion, { texto: string; clase: string; punto: string }> = {
  en_evaluacion: { texto: 'En evaluación', clase: 'bg-sky-50 text-sky-900 ring-sky-200', punto: 'bg-sky-600 animate-latido' },
  pendiente_revision: { texto: 'Pendiente de revisión', clase: 'bg-mango-100 text-mango-800 ring-mango-300', punto: 'bg-mango-500' },
  decidida: { texto: 'Decidida', clase: 'bg-cafetal-50 text-cafetal-800 ring-cafetal-100', punto: 'bg-cafetal-600' },
  error_evaluacion: { texto: 'Error en la evaluación', clase: 'bg-red-50 text-red-800 ring-red-200', punto: 'bg-red-600' },
}

export const VEREDICTOS: Record<Veredicto, { texto: string; clase: string }> = {
  ENTREVISTA: { texto: 'Entrevista', clase: 'bg-caribe-50 text-caribe-800 ring-caribe-200' },
  REVISION_HUMANA: { texto: 'Revisión humana', clase: 'bg-mango-100 text-mango-800 ring-mango-300' },
  NO_CONTINUA: { texto: 'No continúa', clase: 'bg-niebla-100 text-niebla-700 ring-niebla-300' },
}

// Umbrales del veredicto sugerido (PLAN §5): ≥ 75 entrevista, 55–74 revisión, < 55 no continúa.
export type Banda = 'alta' | 'media' | 'baja'
export const bandaPuntaje = (puntaje: number): Banda => (puntaje >= 75 ? 'alta' : puntaje >= 55 ? 'media' : 'baja')
export const COLOR_BANDA: Record<Banda, string> = { alta: 'bg-caribe-500', media: 'bg-mango-400', baja: 'bg-guayaba-400' }

// Llama a `alTick` cada 5 s mientras `activo`; limpia el intervalo al desactivarse o desmontar.
export function useRefresco(activo: boolean, alTick: () => void) {
  useEffect(() => {
    if (!activo) return
    const t = setInterval(alTick, REFRESCO_MS)
    return () => clearInterval(t)
  }, [activo, alTick])
}
