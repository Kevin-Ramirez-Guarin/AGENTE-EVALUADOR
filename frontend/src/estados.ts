import { useEffect } from 'react'
import type { EstadoEvaluacion } from './api'

export const REFRESCO_MS = 5000

export const ESTADOS: Record<EstadoEvaluacion, { texto: string; clase: string }> = {
  en_evaluacion: { texto: 'En evaluación', clase: 'bg-blue-100 text-blue-900' },
  pendiente_revision: { texto: 'Pendiente de revisión', clase: 'bg-amber-100 text-amber-900' },
  decidida: { texto: 'Decidida', clase: 'bg-green-100 text-green-900' },
  error_evaluacion: { texto: 'Error en la evaluación', clase: 'bg-red-100 text-red-900' },
}

// Llama a `alTick` cada 5 s mientras `activo`; limpia el intervalo al desactivarse o desmontar.
export function useRefresco(activo: boolean, alTick: () => void) {
  useEffect(() => {
    if (!activo) return
    const t = setInterval(alTick, REFRESCO_MS)
    return () => clearInterval(t)
  }, [activo, alTick])
}
