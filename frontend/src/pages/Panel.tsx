import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getEvaluaciones, getVacantes, type EvaluacionResumen, type Vacante } from '../api'

const LIMIT = 10
const btn = 'rounded border border-slate-300 bg-white px-3 py-1 disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-indigo-700'

export function Panel() {
  const [vacantes, setVacantes] = useState<Vacante[]>([])
  const [vacanteId, setVacanteId] = useState('')
  const [offset, setOffset] = useState(0)
  const [filas, setFilas] = useState<EvaluacionResumen[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    getVacantes().then(setVacantes, () => setVacantes([]))
  }, [])

  useEffect(() => {
    let vigente = true
    // Se pide una fila de más solo para saber si existe una página siguiente.
    getEvaluaciones({ vacante_id: vacanteId || undefined, limit: LIMIT + 1, offset }).then(
      (f) => vigente && (setFilas(f), setError(false)),
      () => vigente && setError(true),
    )
    return () => {
      vigente = false
    }
  }, [vacanteId, offset])

  // Limpia filas y error para no mostrar datos viejos ni dejar "Siguiente" activo mientras carga.
  const ir = (vacante: string, desde: number) => {
    setFilas(null)
    setError(false)
    setVacanteId(vacante)
    setOffset(desde)
  }
  const hayMas = (filas?.length ?? 0) > LIMIT
  const visibles = filas?.slice(0, LIMIT)

  const titulo = (id: string) => vacantes.find((v) => v.id === id)?.titulo ?? id

  return (
    <section>
      <h1 className="text-2xl font-bold">Panel del reclutador</h1>
      <p className="mt-2 rounded bg-amber-100 px-3 py-2 text-sm text-amber-900">Demo sin autenticación</p>

      <div className="mt-4">
        <label htmlFor="filtro-vacante" className="mr-2 font-medium">Vacante</label>
        <select
          id="filtro-vacante"
          value={vacanteId}
          onChange={(e) => ir(e.target.value, 0)}
          className="rounded border border-slate-300 bg-white px-2 py-1"
        >
          <option value="">Todas</option>
          {vacantes.map((v) => (
            <option key={v.id} value={v.id}>{v.titulo}</option>
          ))}
        </select>
      </div>

      {error && <p role="alert" className="mt-4 text-red-700">No pudimos cargar las evaluaciones. Intenta de nuevo más tarde.</p>}
      {!error && !filas && <p role="status" aria-busy="true" className="mt-4">Cargando evaluaciones…</p>}
      {!error && filas?.length === 0 && <p className="mt-4">No hay evaluaciones para mostrar.</p>}
      {!error && !!visibles?.length && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full border-collapse bg-white text-left text-sm">
            <caption className="sr-only">Evaluaciones ordenadas por puntaje</caption>
            <thead>
              <tr className="border-b border-slate-300">
                {['Candidato', 'Vacante', 'Puntaje', 'Sugerido por la IA', 'Decisión final', 'Estado'].map((h) => (
                  <th key={h} scope="col" className="px-3 py-2 font-semibold">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibles.map((f) => (
                <tr key={f.id} className="border-b border-slate-200">
                  <td className="px-3 py-2">
                    <Link to={`/panel/${f.id}`} className="font-medium text-indigo-800 underline focus-visible:outline-2 focus-visible:outline-indigo-700">{f.candidato}</Link>
                  </td>
                  <td className="px-3 py-2">{titulo(f.vacante_id)}</td>
                  <td className="px-3 py-2">{f.puntaje_total}</td>
                  <td className="px-3 py-2">{f.veredicto_sugerido}</td>
                  <td className="px-3 py-2">{f.veredicto_final ?? '—'}</td>
                  <td className="px-3 py-2">{f.estado}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <nav aria-label="Paginación" className="mt-4 flex gap-2">
        <button type="button" className={btn} disabled={offset === 0} onClick={() => ir(vacanteId, Math.max(0, offset - LIMIT))}>Anterior</button>
        <button type="button" className={btn} disabled={!hayMas} onClick={() => ir(vacanteId, offset + LIMIT)}>Siguiente</button>
      </nav>
    </section>
  )
}
