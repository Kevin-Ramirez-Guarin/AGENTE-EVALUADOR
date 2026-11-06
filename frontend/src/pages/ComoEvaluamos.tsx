import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getVacante, type NombreCriterio, type Vacante } from '../api'
import { DESCRIPCION, ETIQUETA, PESOS_GENERICOS } from '../criterios'
import { enlace } from '../estilos'
import { BandaTitulo } from '../ui'

const CORREO = 'privacidad@giveaway.example'
const DERECHOS = [
  'Conocer qué datos tuyos tenemos y para qué los usamos.',
  'Actualizar tus datos cuando hayan cambiado.',
  'Rectificar los datos que estén errados.',
  'Revocar tu autorización y pedir que borremos tu información.',
  'Pedir la revisión humana de la decisión sobre tu postulación.',
]
// Un color por criterio, el mismo en la barra y en la lista.
const COLOR: Record<NombreCriterio, string> = {
  tecnico: 'bg-caribe-500',
  experiencia: 'bg-cafetal-600',
  blandas: 'bg-mango-400',
  educacion: 'bg-selva-700',
  idiomas: 'bg-guayaba-400',
}
const CRITERIOS = Object.keys(ETIQUETA) as NombreCriterio[]
const h2 = 'text-2xl font-semibold text-selva-900'
const pct = (p: number) => `${Math.round(p * 100)} %`

export function ComoEvaluamos() {
  const [params] = useSearchParams()
  const vacanteId = params.get('vacante')
  const [vacante, setVacante] = useState<Vacante | null>(null)

  useEffect(() => {
    if (!vacanteId) return
    let vigente = true
    // Si la vacante no existe o falla la API, se quedan los pesos genéricos.
    getVacante(vacanteId).then((v) => vigente && setVacante(v), () => undefined)
    return () => {
      vigente = false
    }
  }, [vacanteId])

  const pesos = (vacanteId && vacante?.pesos) || PESOS_GENERICOS

  return (
    <>
      <BandaTitulo titulo="Cómo evaluamos tu hoja de vida">
        <p className="max-w-2xl text-lg leading-relaxed text-caribe-100">
          La IA recomienda, una persona del equipo de Talento decide. Aquí te contamos qué miramos, quién toma la
          decisión y qué datos tuyos nunca ve la IA.
        </p>
      </BandaTitulo>

      <article className="mx-auto max-w-3xl space-y-14 px-4 py-12 sm:px-6 sm:py-16">
        <section aria-labelledby="h-que" className="space-y-5">
          <h2 id="h-que" className={h2}>Qué miramos</h2>
          <p className="leading-relaxed text-niebla-700">
            {vacanteId && vacante ? `Para la vacante ${vacante.titulo}` : 'En general'}, evaluamos cinco criterios. El
            porcentaje indica cuánto pesa cada uno en el puntaje final.
          </p>
          <div aria-hidden="true" className="flex h-3 gap-0.5 overflow-hidden rounded-full">
            {CRITERIOS.map((c) => <span key={c} className={COLOR[c]} style={{ flexGrow: pesos[c] }} />)}
          </div>
          <ul aria-label="Criterios de evaluación" className="divide-y divide-niebla-200 rounded-xl bg-white shadow-tarjeta ring-1 ring-niebla-200">
            {CRITERIOS.map((c) => (
              <li key={c} className="grid grid-cols-[auto_1fr_auto] items-baseline gap-x-3 gap-y-1 p-4 sm:p-5">
                <span aria-hidden="true" className={`size-2.5 translate-y-[-1px] rounded-full ${COLOR[c]}`} />
                <strong className="font-semibold text-selva-900">{ETIQUETA[c]}</strong>
                <span className="font-display text-xl font-semibold tabular-nums text-selva-900">{pct(pesos[c])}</span>
                <p className="col-start-2 col-end-4 text-sm leading-relaxed text-niebla-700">{DESCRIPCION[c]}</p>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="h-quien" className="space-y-5">
          <h2 id="h-quien" className={h2}>Quién decide</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl bg-white p-5 ring-1 ring-niebla-200">
              <h3 className="font-semibold text-selva-900">La IA</h3>
              <p className="mt-2 leading-relaxed text-niebla-700">La IA solo extrae información y sugiere un resultado a partir de tu hoja de vida. Nunca rechaza a nadie por sí sola.</p>
            </div>
            <div className="rounded-xl bg-caribe-50 p-5 ring-1 ring-caribe-200">
              <h3 className="font-semibold text-selva-900">El equipo de Talento</h3>
              <p className="mt-2 leading-relaxed text-niebla-700">Una persona decide: el equipo de Talento revisa la explicación y toma la decisión final antes de escribirte.</p>
            </div>
          </div>
        </section>

        <section aria-labelledby="h-datos" className="space-y-5">
          <h2 id="h-datos" className={h2}>Lo que la IA no ve</h2>
          <p className="border-l-4 border-mango-400 pl-5 leading-relaxed text-niebla-700">
            Antes de que la IA lea tu hoja de vida, quitamos tus datos de identificación y contacto (nombre, correo,
            teléfono, documento, edad, estado civil y origen) y neutralizamos las palabras que revelan el género, para
            que esos datos no influyan en la sugerencia.
          </p>
        </section>

        <section aria-labelledby="h-derechos" className="space-y-5">
          <h2 id="h-derechos" className={h2}>Tus derechos</h2>
          <p className="leading-relaxed text-niebla-700">Según la Ley 1581 de 2012 de protección de datos personales, puedes:</p>
          <ul aria-label="Tus derechos" className="space-y-2">
            {DERECHOS.map((d) => (
              <li key={d} className="flex items-start gap-3 text-niebla-700">
                <span aria-hidden="true" className="mt-2.5 size-1.5 shrink-0 rounded-full bg-caribe-500" />
                {d}
              </li>
            ))}
          </ul>
          <p className="leading-relaxed text-niebla-700">
            Para ejercerlos escríbenos a <a href={`mailto:${CORREO}`} className={enlace}>{CORREO}</a> indicando tu nombre y
            la vacante a la que te postulaste.
          </p>
          <p className="text-sm text-niebla-600">
            Este correo es un canal de demostración: esto es un proyecto académico y Giveaway es una empresa ficticia.
          </p>
        </section>
      </article>
    </>
  )
}
