import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ApiError,
  decidir,
  getEvaluacion,
  getVacante,
  reintentarEvaluacion,
  type CriterioDetalle,
  type EstadoEvaluacion,
  type DecisionRespuesta,
  type EvaluacionDetalle,
  type Habilidad,
  type NombreCriterio,
  type Perfil,
  type Resultado,
  type Veredicto,
} from '../api'
import { ETIQUETA } from '../criterios'
import { bandaPuntaje, COLOR_BANDA, ESTADOS, useRefresco, VEREDICTOS } from '../estados'
import { boton, campoClase, enlace } from '../estilos'
import { Campo, EstadoInsignia, IconoAlerta, IconoCheck, IconoMenos, IconoVolver } from '../ui'

const OPCIONES: Veredicto[] = ['ENTREVISTA', 'REVISION_HUMANA', 'NO_CONTINUA']
const CLAVE_RECLUTADOR = 'reclutador'
const tarjeta = 'rounded-xl bg-white p-5 shadow-tarjeta ring-1 ring-niebla-200 sm:p-6'
const h2 = 'text-xl font-semibold text-selva-900'
const textoVeredicto = (v: Veredicto | null | undefined) => (v ? VEREDICTOS[v]?.texto ?? v : '—')

const Lista = ({ titulo, items, icono, Encabezado = 'h4' }: { titulo: string; items: string[]; icono?: ReactNode; Encabezado?: 'h3' | 'h4' }) =>
  items.length === 0 ? null : (
    <div>
      <Encabezado className="text-sm font-semibold text-niebla-700">{titulo}</Encabezado>
      <ul className="mt-1.5 space-y-1 text-sm text-niebla-900">
        {items.map((i, n) => (
          <li key={n} className="flex items-start gap-1.5">
            {icono ?? <span aria-hidden="true" className="mt-2 size-1 shrink-0 rounded-full bg-niebla-500" />}
            {i}
          </li>
        ))}
      </ul>
    </div>
  )

const Evidencias = ({ items }: { items: string[] }) =>
  items.length === 0 ? null : (
    <div>
      <h4 className="text-sm font-semibold text-niebla-700">Evidencias</h4>
      <ul className="mt-1.5 space-y-1.5 text-sm text-niebla-700">
        {items.map((i, n) => <li key={n} className="border-l-2 border-caribe-200 pl-2.5"><q>{i}</q></li>)}
      </ul>
    </div>
  )

// Barra de 0 a 100 coloreada según la banda del puntaje; el valor exacto va en aria-valuetext.
function Barra({ valor, etiqueta, etiquetadaPor, umbrales = false }: { valor: number; etiqueta?: string; etiquetadaPor?: string; umbrales?: boolean }) {
  return (
    <div
      role="meter"
      aria-label={etiqueta}
      aria-labelledby={etiquetadaPor}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={valor}
      aria-valuetext={`${valor} de 100`}
      className="relative h-2.5 overflow-hidden rounded-full bg-niebla-200"
    >
      <div className={`h-full rounded-full ${COLOR_BANDA[bandaPuntaje(valor)]}`} style={{ width: `${Math.min(100, Math.max(0, valor))}%` }} />
      {umbrales && [55, 75].map((u) => <span key={u} aria-hidden="true" className="absolute inset-y-0 w-0.5 bg-white" style={{ left: `${u}%` }} />)}
    </div>
  )
}

const Habilidades = ({ titulo, items }: { titulo: string; items: Habilidad[] }) => (
  <div>
    <h3 className="font-semibold text-selva-900">{titulo}</h3>
    {items.length === 0 && <p className="mt-1 text-sm text-niebla-600">Sin datos.</p>}
    <ul className="mt-2 space-y-2.5 text-sm">
      {items.map((h, n) => (
        <li key={n}>
          <span className="font-semibold text-niebla-900">{h.nombre}</span>{' '}
          <span className="rounded-md bg-niebla-100 px-1.5 py-0.5 text-xs font-medium text-niebla-700">{h.nivel}</span>
          <span className="mt-0.5 block text-niebla-700">Evidencia: <q>{h.evidencia}</q></span>
        </li>
      ))}
    </ul>
  </div>
)

function Criterio({ c }: { c: CriterioDetalle }) {
  const nombre = ETIQUETA[c.criterio]
  return (
    <li className={`${tarjeta} space-y-4`}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h3 className="font-semibold text-selva-900">
          {nombre}
          {c.peso > 0 && <span className="ml-2 text-sm font-normal text-niebla-600">Peso {Math.round(c.peso * 100)} %</span>}
        </h3>
        <span aria-hidden="true" className="font-display text-lg font-semibold tabular-nums text-selva-900">{c.puntaje} / 100</span>
      </div>
      <Barra valor={c.puntaje} etiqueta={`Puntaje ${nombre}`} />
      {(c.cumplidos.length > 0 || c.faltantes.length > 0 || c.evidencias.length > 0) && (
        <div className="grid gap-4 sm:grid-cols-3">
          <Lista titulo="Cumplido" items={c.cumplidos} icono={<IconoCheck className="mt-0.5 size-4 shrink-0 text-cafetal-600" />} />
          <Lista titulo="Faltante" items={c.faltantes} icono={<IconoMenos className="mt-0.5 size-4 shrink-0 text-red-700" />} />
          <Evidencias items={c.evidencias} />
        </div>
      )}
      {c.nota && (
        <p className="rounded-lg bg-niebla-50 p-3 text-sm text-niebla-700">
          <span className="font-semibold text-niebla-900">Nota para la persona candidata (se usa en el correo): </span>
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

function Resumen({ r }: { r: Resultado }) {
  const sugerido = VEREDICTOS[r.veredicto_sugerido]
  return (
    <section aria-labelledby="h-eval" className={`${tarjeta} space-y-4`}>
      <h2 id="h-eval" className={h2}>Evaluación de la IA</h2>
      <div className="space-y-2">
        <p id="etiqueta-total" className="text-sm font-semibold text-niebla-600">Puntaje total</p>
        <p aria-hidden="true" className="font-display text-5xl leading-none font-semibold tracking-tight tabular-nums text-selva-900">
          {r.puntaje_total}
          <span className="ml-1 text-lg font-medium text-niebla-600">/ 100</span>
        </p>
        <Barra valor={r.puntaje_total} etiquetadaPor="etiqueta-total" umbrales />
        <p className="text-xs text-niebla-600">Líneas en 55 (revisión humana) y 75 (entrevista).</p>
      </div>
      <p className={`flex items-center gap-2 text-sm font-semibold ${r.cumple_obligatorios ? 'text-cafetal-800' : 'text-red-800'}`}>
        {r.cumple_obligatorios ? <IconoCheck className="size-5 shrink-0" /> : <IconoAlerta className="size-5 shrink-0" />}
        Cumple los obligatorios: {r.cumple_obligatorios ? 'Sí' : 'No'}
      </p>
      <p className={`rounded-lg px-3 py-2.5 font-semibold ring-1 ring-inset ${sugerido?.clase ?? 'bg-niebla-100 ring-niebla-300'}`}>
        La IA sugiere: {textoVeredicto(r.veredicto_sugerido)}
      </p>
      <p className="text-sm leading-relaxed text-niebla-700">{r.explicacion}</p>
      {r.mejor_vacante_alternativa && (
        <p className="text-sm text-niebla-700">Vacante alternativa sugerida: <strong className="font-semibold text-niebla-900">{r.mejor_vacante_alternativa}</strong></p>
      )}
    </section>
  )
}

function PerfilCandidato({ p }: { p: Perfil }) {
  const idiomas = p.idiomas.map((i) => `${i.idioma} ${i.nivel}`).join(', ')
  return (
    <section aria-labelledby="h-perfil" className={`${tarjeta} space-y-5`}>
      <h2 id="h-perfil" className={h2}>Perfil</h2>
      <p className="leading-relaxed text-niebla-900">{p.resumen}</p>
      <dl className="grid grid-cols-2 gap-4 rounded-lg bg-niebla-50 p-4 text-sm sm:grid-cols-3">
        <div><dt className="text-niebla-600">Experiencia</dt><dd className="font-semibold tabular-nums">{p.anios_experiencia} {p.anios_experiencia === 1 ? 'año' : 'años'}</dd></div>
        <div><dt className="text-niebla-600">Nivel educativo</dt><dd className="font-semibold capitalize">{p.nivel_educativo}</dd></div>
        {idiomas && <div><dt className="text-niebla-600">Idiomas</dt><dd className="font-semibold">{idiomas}</dd></div>}
      </dl>
      <div className="grid gap-4 sm:grid-cols-2">
        <Lista titulo="Fortalezas" items={p.fortalezas} Encabezado="h3" />
        <Lista titulo="Debilidades" items={p.debilidades} Encabezado="h3" />
      </div>
      <div className="grid gap-6 border-t border-niebla-200 pt-5 sm:grid-cols-2">
        <Habilidades titulo="Habilidades técnicas" items={p.habilidades_tecnicas} />
        <Habilidades titulo="Habilidades blandas" items={p.habilidades_blandas} />
      </div>
    </section>
  )
}

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
  const [tituloVacante, setTituloVacante] = useState<string | null>(null)
  const actualizar = useCallback(() => setRecarga((n) => n + 1), [])
  useRefresco(ev?.estado === 'en_evaluacion', actualizar)

  useEffect(() => {
    let vigente = true
    getEvaluacion(evalId).then(
      (e) => vigente && (setEv(e), setErrorCarga(''), e.resultado && setVeredicto(e.resultado.veredicto_sugerido)),
      (e) => vigente && setErrorCarga(e instanceof ApiError && e.status === 404 ? MENSAJE_ERROR[404] : 'No pudimos cargar la evaluación. Intenta de nuevo más tarde.'),
    )
    return () => {
      vigente = false
    }
  }, [evalId, recarga])

  // Título legible de la vacante; si la búsqueda falla se queda el id.
  const vacanteId = ev?.vacante_id
  useEffect(() => {
    if (!vacanteId) return
    let vigente = true
    getVacante(vacanteId).then((v) => vigente && setTituloVacante(v.titulo), () => undefined)
    return () => {
      vigente = false
    }
  }, [vacanteId])

  const volver = (
    <Link to="/panel" className="-ml-1 inline-flex items-center gap-1 rounded-md py-1 pr-2 text-sm font-medium text-caribe-800 hover:text-selva-900">
      <IconoVolver className="size-4" />
      Volver al panel
    </Link>
  )

  if (errorCarga && !ev) return <div className="space-y-4">{volver}<p role="alert" className="rounded-xl bg-red-50 p-4 text-red-800 ring-1 ring-red-200">{errorCarga}</p></div>
  if (!ev) return <p role="status" className="text-niebla-600">Cargando evaluación…</p>

  const { perfil, resultado } = ev
  const final = decision?.veredicto_final ?? ev.veredicto_final
  const decidida = decision !== null || ev.estado === 'decidida'
  const estado = decision?.estado ?? ev.estado
  const difiere = !!resultado && veredicto !== resultado.veredicto_sugerido

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

  const resultadoDecision = (
    <div role="status" className="space-y-1 rounded-lg bg-cafetal-50 p-4 text-sm text-cafetal-800 ring-1 ring-cafetal-100">
      <p className="font-semibold">Estado: {ESTADOS[estado as EstadoEvaluacion]?.texto ?? estado}</p>
      <p>Veredicto final: {textoVeredicto(final)}</p>
      {decision?.entrevista && (
        <p>
          Entrevista: {new Date(decision.entrevista.inicio).toLocaleString('es-CO')} —{' '}
          {decision.entrevista.meet_link.startsWith('https://') ? (
            <a href={decision.entrevista.meet_link} target="_blank" rel="noopener noreferrer" className={enlace}>Enlace de Meet</a>
          ) : (
            'enlace de Meet no disponible'
          )}
        </p>
      )}
    </div>
  )

  return (
    <article className="space-y-6">
      {volver}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-[-0.02em] text-selva-900">{ev.candidato}</h1>
          <p className="mt-1 text-niebla-600">Vacante: {tituloVacante ?? ev.vacante_id}</p>
        </div>
        <EstadoInsignia estado={estado as EstadoEvaluacion} />
      </header>

      {ev.estado === 'en_evaluacion' && (
        <p role="status" className="flex items-center gap-3 rounded-xl bg-sky-50 p-4 text-sky-900 ring-1 ring-sky-200">
          <span aria-hidden="true" className="size-2 shrink-0 animate-latido rounded-full bg-sky-600" />
          La IA está analizando esta hoja de vida… Esta página se actualiza sola.
        </p>
      )}
      {ev.estado === 'error_evaluacion' && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-red-50 p-4 text-red-800 ring-1 ring-red-200">
          <p className="flex items-start gap-2">
            <IconoAlerta className="mt-0.5 size-5 shrink-0" />
            {ev.error ?? 'La evaluación falló.'}
          </p>
          <button type="button" onClick={reintentar} className={boton('peligro', 'compacto')}>Reintentar</button>
        </div>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_24rem] lg:grid-rows-[auto_1fr]">
        {resultado && <div className="lg:col-start-2 lg:row-start-1"><Resumen r={resultado} /></div>}

        {perfil && resultado && (
          <div className="space-y-6 lg:col-start-1 lg:row-span-2 lg:row-start-1">
            <section aria-labelledby="h-criterios" className="space-y-3">
              <h2 id="h-criterios" className={h2}>Detalle por criterio</h2>
              <ul className="space-y-3">
                {criteriosDe(resultado).map((c) => <Criterio key={c.criterio} c={c} />)}
              </ul>
            </section>
            <PerfilCandidato p={perfil} />
          </div>
        )}

        {ev.estado === 'decidida' && (
          <section aria-labelledby="h-decision" className={`${tarjeta} space-y-3 lg:col-start-2`}>
            <h2 id="h-decision" className={h2}>Decisión registrada</h2>
            {resultadoDecision}
          </section>
        )}

        {ev.estado === 'pendiente_revision' && (
          <section aria-labelledby="h-decision" className="space-y-4 rounded-xl bg-white p-5 shadow-elevada ring-2 ring-caribe-700 sm:p-6 lg:col-start-2">
            <div>
              <h2 id="h-decision" className={h2}>Tu decisión</h2>
              <p className="mt-1 font-medium text-niebla-700">La IA recomienda; la decisión es tuya.</p>
            </div>
            <form onSubmit={enviar} noValidate className="space-y-4">
              <Campo id="reclutador" label="Nombre del reclutador">
                <input id="reclutador" value={reclutador} maxLength={100} disabled={decidida} autoComplete="name" onChange={(e) => setReclutador(e.target.value)} className={campoClase} />
              </Campo>
              <Campo id="veredicto" label="Veredicto">
                <select id="veredicto" value={decidida && final ? final : veredicto} disabled={decidida} onChange={(e) => setVeredicto(e.target.value as Veredicto)} className={campoClase}>
                  {OPCIONES.map((v) => (
                    <option key={v} value={v}>{VEREDICTOS[v].texto}{v === resultado?.veredicto_sugerido ? ' (sugerido por la IA)' : ''}</option>
                  ))}
                </select>
              </Campo>
              <Campo id="motivo" label="Motivo (obligatorio si difiere del sugerido)">
                <textarea id="motivo" rows={3} value={motivo} maxLength={1000} disabled={decidida} aria-required={difiere} onChange={(e) => setMotivo(e.target.value)} className={campoClase} />
              </Campo>
              {error && <p role="alert" className="flex items-start gap-1.5 text-sm font-medium text-red-700"><IconoAlerta className="mt-0.5 size-4 shrink-0" />{error}</p>}
              <button type="submit" disabled={decidida || enviando} className={`${boton('primario')} w-full`}>
                {enviando ? 'Registrando…' : 'Registrar decisión'}
              </button>
              <p className="text-xs text-niebla-600">Al registrarla se envía el correo a la persona candidata y, si es entrevista, se agenda.</p>
            </form>
            {decidida && resultadoDecision}
          </section>
        )}
      </div>
    </article>
  )
}
