import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ApiError,
  decidir,
  getEvaluacion,
  reintentarEvaluacion,
  type CriterioDetalle,
  type DecisionRespuesta,
  type EvaluacionDetalle,
  type Habilidad,
  type NombreCriterio,
  type Resultado,
  type Veredicto,
} from '../api'
import { useRefresco } from '../estados'

const VEREDICTOS: Veredicto[] = ['ENTREVISTA', 'REVISION_HUMANA', 'NO_CONTINUA']
const ETIQUETA: Record<NombreCriterio, string> = {
  tecnico: 'Técnico',
  experiencia: 'Experiencia',
  blandas: 'Habilidades blandas',
  educacion: 'Educación',
  idiomas: 'Idiomas',
}
const CLAVE_RECLUTADOR = 'reclutador'
const campo = 'mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 disabled:bg-slate-100'

const Lista = ({ titulo, items }: { titulo: string; items: string[] }) =>
  items.length === 0 ? null : (
    <div>
      <h4 className="text-sm font-semibold text-slate-700">{titulo}</h4>
      <ul className="list-inside list-disc text-sm">
        {items.map((i, n) => <li key={n}>{i}</li>)}
      </ul>
    </div>
  )

const Habilidades = ({ titulo, items }: { titulo: string; items: Habilidad[] }) => (
  <div>
    <h3 className="font-semibold">{titulo}</h3>
    {items.length === 0 && <p className="text-sm text-slate-600">Sin datos.</p>}
    <ul className="space-y-1 text-sm">
      {items.map((h, n) => (
        <li key={n}>
          <strong>{h.nombre}</strong> ({h.nivel}) — evidencia: <q>{h.evidencia}</q>
        </li>
      ))}
    </ul>
  </div>
)

function Criterio({ c }: { c: CriterioDetalle }) {
  const nombre = ETIQUETA[c.criterio]
  return (
    <li className="space-y-2 rounded border border-slate-200 bg-white p-3">
      <h3 className="font-semibold">
        {nombre}
        {c.peso > 0 && <span className="text-sm font-normal text-slate-600"> Peso {Math.round(c.peso * 100)} %</span>}
      </h3>
      <div className="flex items-center gap-2">
        <div
          role="meter"
          aria-label={`Puntaje ${nombre}`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={c.puntaje}
          aria-valuetext={`${c.puntaje} de 100`}
          className="h-3 flex-1 overflow-hidden rounded bg-slate-200"
        >
          <div className="h-full bg-indigo-700" style={{ width: `${c.puntaje}%` }} />
        </div>
        <span aria-hidden="true" className="w-16 text-sm">{c.puntaje} / 100</span>
      </div>
      <Lista titulo="Cumplido" items={c.cumplidos} />
      <Lista titulo="Faltante" items={c.faltantes} />
      <Lista titulo="Evidencias" items={c.evidencias} />
      {c.nota && (
        <p className="text-sm">
          <span className="font-semibold">Nota para la persona candidata (se usa en el correo): </span>
          <i>{c.nota}</i>
        </p>
      )}
    </li>
  )
}

// Si el backend no manda `criterios`, se reconstruyen solo con el puntaje.
const criteriosDe = (r: Resultado): CriterioDetalle[] =>
  r.criterios?.length
    ? r.criterios
    : (Object.entries(r.puntajes_por_criterio) as [NombreCriterio, number][]).map(([criterio, puntaje]) => ({
        criterio, puntaje, peso: 0, cumplidos: [], faltantes: [], evidencias: [], nota: '',
      }))

const MENSAJE_ERROR: Record<number, string> = {
  409: 'Esta evaluación ya fue decidida; no se puede decidir de nuevo.',
  422: 'Datos inválidos: el motivo es obligatorio si tu veredicto difiere del sugerido, y escribe tu nombre.',
  404: 'La evaluación no existe.',
}

// `key={id}` reinicia todo el estado (formulario, decisión, errores) al cambiar de evaluación.
export function Detalle() {
  const { id } = useParams()
  return <DetalleEvaluacion key={id} evalId={Number(id)} />
}

function DetalleEvaluacion({ evalId }: { evalId: number }) {
  const [ev, setEv] = useState<EvaluacionDetalle | null>(null)
  const [errorCarga, setErrorCarga] = useState('')
  const [veredicto, setVeredicto] = useState<Veredicto>('ENTREVISTA')
  const [motivo, setMotivo] = useState('')
  const [reclutador, setReclutador] = useState(() => localStorage.getItem(CLAVE_RECLUTADOR) ?? '')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [decision, setDecision] = useState<DecisionRespuesta | null>(null)
  const [recarga, setRecarga] = useState(0)
  const actualizar = useCallback(() => setRecarga((n) => n + 1), [])
  useRefresco(ev?.estado === 'en_evaluacion', actualizar)

  useEffect(() => {
    let vigente = true
    getEvaluacion(evalId).then(
      (e) => vigente && (setEv(e), e.resultado && setVeredicto(e.resultado.veredicto_sugerido)),
      (e) => vigente && setErrorCarga(e instanceof ApiError && e.status === 404 ? MENSAJE_ERROR[404] : 'No pudimos cargar la evaluación. Intenta de nuevo más tarde.'),
    )
    return () => {
      vigente = false
    }
  }, [evalId, recarga])

  if (errorCarga) return <p role="alert" className="text-red-700">{errorCarga}</p>
  if (!ev) return <p role="status">Cargando evaluación…</p>

  const { perfil, resultado } = ev
  const final = decision?.veredicto_final ?? ev.veredicto_final
  const decidida = decision !== null || ev.estado === 'decidida'
  const estado = decision?.estado ?? ev.estado

  // 202 o 409: en ambos casos se recarga para mostrar el estado real.
  async function reintentar() {
    await reintentarEvaluacion(evalId).catch(() => undefined)
    actualizar()
  }

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setError('')
    const nombre = reclutador.trim()
    const razon = motivo.trim()
    if (!nombre) return setError('Escribe tu nombre como reclutador.')
    if (veredicto !== resultado?.veredicto_sugerido && !razon) {
      return setError('Escribe el motivo: es obligatorio cuando tu veredicto difiere del sugerido por la IA.')
    }
    if (!window.confirm('Se enviará un correo al candidato. ¿Confirmas la decisión?')) return
    setEnviando(true)
    try {
      setDecision(await decidir(evalId, { veredicto, motivo: razon || undefined, reclutador: nombre }))
      localStorage.setItem(CLAVE_RECLUTADOR, nombre)
    } catch (err) {
      setError(err instanceof ApiError && MENSAJE_ERROR[err.status] ? MENSAJE_ERROR[err.status] : 'No pudimos registrar la decisión. Intenta de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <article className="space-y-6">
      <Link to="/panel" className="text-indigo-800 underline">← Volver al panel</Link>
      <header>
        <h1 className="text-2xl font-bold">{ev.candidato}</h1>
        <p className="text-slate-600">Vacante: {ev.vacante_id}</p>
      </header>

      {ev.estado === 'en_evaluacion' && (
        <p role="status" className="rounded bg-blue-100 px-3 py-2 text-blue-900">La IA está analizando esta hoja de vida… Esta página se actualiza sola.</p>
      )}
      {ev.estado === 'error_evaluacion' && (
        <div role="alert" className="space-y-2 rounded bg-red-100 px-3 py-2 text-red-900">
          <p>{ev.error ?? 'La evaluación falló.'}</p>
          <button type="button" onClick={reintentar} className="rounded bg-red-800 px-4 py-2 font-medium text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-800">
            Reintentar
          </button>
        </div>
      )}

      {perfil && resultado && (<>
      <section aria-labelledby="h-perfil" className="space-y-3">
        <h2 id="h-perfil" className="text-xl font-semibold">Perfil</h2>
        <p>{perfil.resumen}</p>
        <Lista titulo="Fortalezas" items={perfil.fortalezas} />
        <Lista titulo="Debilidades" items={perfil.debilidades} />
        <Habilidades titulo="Habilidades técnicas" items={perfil.habilidades_tecnicas} />
        <Habilidades titulo="Habilidades blandas" items={perfil.habilidades_blandas} />
      </section>

      <section aria-labelledby="h-eval" className="space-y-3">
        <h2 id="h-eval" className="text-xl font-semibold">Evaluación de la IA</h2>
        <p className="text-lg font-semibold">Puntaje total: {resultado.puntaje_total}</p>
        <p>Cumple los obligatorios: {resultado.cumple_obligatorios ? 'Sí' : 'No'}</p>
        <p>La IA sugiere: {resultado.veredicto_sugerido}</p>
        <ul className="space-y-3">
          {criteriosDe(resultado).map((c) => <Criterio key={c.criterio} c={c} />)}
        </ul>
        <p>{resultado.explicacion}</p>
        {resultado.mejor_vacante_alternativa && <p>Vacante alternativa sugerida: {resultado.mejor_vacante_alternativa}</p>}
      </section>

      </>)}

      {ev.estado === 'decidida' && (
        <div role="status" className="space-y-1">
          <p>Estado: {estado}</p>
          <p>Veredicto final: {final}</p>
        </div>
      )}

      {ev.estado === 'pendiente_revision' && (
      <section aria-labelledby="h-decision" className="space-y-3 rounded border border-indigo-200 bg-indigo-50 p-4">
        <h2 id="h-decision" className="text-xl font-semibold">Tu decisión</h2>
        <p className="font-medium">La IA recomienda; la decisión es tuya.</p>
        <form onSubmit={enviar} noValidate className="space-y-3">
          <div>
            <label htmlFor="reclutador">Nombre del reclutador</label>
            <input id="reclutador" value={reclutador} maxLength={100} disabled={decidida} onChange={(e) => setReclutador(e.target.value)} className={campo} />
          </div>
          <div>
            <label htmlFor="veredicto">Veredicto</label>
            <select id="veredicto" value={decidida && final ? final : veredicto} disabled={decidida} onChange={(e) => setVeredicto(e.target.value as Veredicto)} className={campo}>
              {VEREDICTOS.map((v) => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="motivo">Motivo (obligatorio si difiere del sugerido)</label>
            <textarea id="motivo" value={motivo} maxLength={1000} disabled={decidida} onChange={(e) => setMotivo(e.target.value)} className={campo} />
          </div>
          {error && <p role="alert" className="text-red-700">{error}</p>}
          <button type="submit" disabled={decidida || enviando} className="rounded bg-indigo-700 px-4 py-2 font-medium text-white disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700">
            Registrar decisión
          </button>
        </form>
        {decidida && (
          <div role="status" className="space-y-1">
            <p>Estado: {estado}</p>
            <p>Veredicto final: {final}</p>
            {decision?.entrevista && (
              <p>
                Entrevista: {new Date(decision.entrevista.inicio).toLocaleString('es-CO')} —{' '}
                {decision.entrevista.meet_link.startsWith('https://') ? (
                  <a href={decision.entrevista.meet_link} target="_blank" rel="noopener noreferrer" className="text-indigo-800 underline">Enlace de Meet</a>
                ) : (
                  'enlace de Meet no disponible'
                )}
              </p>
            )}
          </div>
        )}
      </section>
      )}
    </article>
  )
}
