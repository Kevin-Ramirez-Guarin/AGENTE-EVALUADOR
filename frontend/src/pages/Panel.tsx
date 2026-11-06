import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getEvaluaciones, getVacantes, type EvaluacionResumen, type Vacante } from '../api'
import { bandaPuntaje, COLOR_BANDA, useRefresco } from '../estados'
import { boton } from '../estilos'
import { EstadoInsignia, IconoRefrescar, Insignia, VeredictoInsignia } from '../ui'

const LIMIT = 10
const COLUMNAS = ['Candidato', 'Vacante', 'Puntaje', 'Sugerido por la IA', 'Decisión final', 'Estado']
const Vacio = () => <span className="text-niebla-600">—</span>

function Puntaje({ valor }: { valor: number | null }) {
  if (valor === null) return <Vacio />
  return (
    <span className="flex items-center gap-2.5">
      <span className="w-10 text-right font-semibold tabular-nums text-selva-900">{valor}</span>
      <span aria-hidden="true" className="h-1.5 w-14 overflow-hidden rounded-full bg-niebla-200">
        <span className={`block h-full rounded-full ${COLOR_BANDA[bandaPuntaje(valor)]}`} style={{ width: `${valor}%` }} />
      </span>
    </span>
  )
}

export function Panel() {
  const [vacantes, setVacantes] = useState<Vacante[]>([])
  const [vacanteId, setVacanteId] = useState('')
  const [offset, setOffset] = useState(0)
  const [filas, setFilas] = useState<EvaluacionResumen[] | null>(null)
  const [error, setError] = useState(false)
  const [recarga, setRecarga] = useState(0)

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
  }, [vacanteId, offset, recarga])

  // Limpia filas y error para no mostrar datos viejos ni dejar "Siguiente" activo mientras carga.
  const ir = (vacante: string, desde: number) => {
    setFilas(null)
    setError(false)
    setVacanteId(vacante)
    setOffset(desde)
  }
  // Un fallo del refresco automático no reemplaza filas ya cargadas.
  const hayError = error && !filas
  const actualizar = useCallback(() => setRecarga((n) => n + 1), [])
  useRefresco(!!filas?.some((f) => f.estado === 'en_evaluacion'), actualizar)
  const hayMas = (filas?.length ?? 0) > LIMIT
  const visibles = filas?.slice(0, LIMIT)

  const titulo = (id: string) => vacantes.find((v) => v.id === id)?.titulo ?? id
  const tarjeta = 'rounded-xl bg-white p-6 ring-1 ring-niebla-200'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-[-0.02em] text-selva-900">Evaluaciones</h1>
          <p className="mt-1 text-niebla-600">La IA recomienda, una persona del equipo de Talento decide.</p>
        </div>
        <Insignia clase="bg-mango-100 text-mango-800 ring-mango-300" punto="bg-mango-500">Demo sin autenticación</Insignia>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-full sm:w-72">
          <label htmlFor="filtro-vacante" className="block text-sm font-semibold text-niebla-700">Vacante</label>
          <select
            id="filtro-vacante"
            value={vacanteId}
            onChange={(e) => ir(e.target.value, 0)}
            className="mt-1 block min-h-10 w-full rounded-md border border-niebla-500 bg-white px-3 text-niebla-900"
          >
            <option value="">Todas</option>
            {vacantes.map((v) => (
              <option key={v.id} value={v.id}>{v.titulo}</option>
            ))}
          </select>
        </div>
        <button type="button" className={`${boton('secundario', 'compacto')} min-h-10`} onClick={actualizar}>
          <IconoRefrescar className="size-4" />
          Actualizar
        </button>
      </div>

      {hayError && <p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800 ring-1 ring-red-200">No pudimos cargar las evaluaciones. Intenta de nuevo más tarde.</p>}
      {!hayError && !filas && <p role="status" aria-busy="true" className={`${tarjeta} text-niebla-600`}>Cargando evaluaciones…</p>}
      {!hayError && filas?.length === 0 && <p className={`${tarjeta} text-niebla-700`}>No hay evaluaciones para mostrar. Cuando alguien se postule, aparecerá aquí.</p>}
      {!hayError && !!visibles?.length && (
        // tabIndex: en pantallas angostas la tabla se desplaza y debe poder recorrerse con teclado.
        <div role="region" aria-labelledby="titulo-tabla" tabIndex={0} className="overflow-x-auto rounded-xl bg-white shadow-tarjeta ring-1 ring-niebla-200">
          <table className="w-full min-w-[50rem] border-collapse text-left text-sm">
            <caption id="titulo-tabla" className="sr-only">Evaluaciones ordenadas por puntaje</caption>
            <thead className="bg-niebla-50 text-niebla-700">
              <tr>
                {COLUMNAS.map((h) => (
                  <th key={h} scope="col" className="px-4 py-3 font-semibold first:sticky first:left-0 first:bg-niebla-50 first:pl-5">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-niebla-200">
              {visibles.map((f) => (
                <tr key={f.id} className="group transition-colors duration-150 hover:bg-niebla-50">
                  {/* La columna del nombre queda fija al desplazar la tabla en pantallas angostas. */}
                  <td className="sticky left-0 bg-white py-3.5 pr-4 pl-5 whitespace-nowrap transition-colors duration-150 group-hover:bg-niebla-50">
                    <Link to={`/panel/${f.id}`} className="font-semibold text-caribe-800 underline-offset-4 hover:underline">{f.candidato}</Link>
                  </td>
                  <td className="px-4 py-3.5 text-niebla-700">{titulo(f.vacante_id)}</td>
                  <td className="px-4 py-3.5"><Puntaje valor={f.puntaje_total} /></td>
                  <td className="px-4 py-3.5">{f.veredicto_sugerido ? <VeredictoInsignia veredicto={f.veredicto_sugerido} /> : <Vacio />}</td>
                  <td className="px-4 py-3.5">{f.veredicto_final ? <VeredictoInsignia veredicto={f.veredicto_final} /> : <Vacio />}</td>
                  <td className="px-4 py-3.5"><EstadoInsignia estado={f.estado} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <nav aria-label="Paginación" className="flex items-center justify-end gap-2">
        <span className="mr-2 text-sm text-niebla-600">Página {offset / LIMIT + 1}</span>
        <button type="button" className={boton('secundario', 'compacto')} disabled={offset === 0} onClick={() => ir(vacanteId, Math.max(0, offset - LIMIT))}>Anterior</button>
        <button type="button" className={boton('secundario', 'compacto')} disabled={!hayMas} onClick={() => ir(vacanteId, offset + LIMIT)}>Siguiente</button>
      </nav>
    </div>
  )
}

