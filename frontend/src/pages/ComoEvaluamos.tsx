import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getVacante, type NombreCriterio, type Vacante } from '../api'
import { DESCRIPCION, ETIQUETA, PESOS_GENERICOS } from '../criterios'

const CORREO = 'privacidad@nexodigital.example'
const DERECHOS = [
  'Conocer qué datos tuyos tenemos y para qué los usamos.',
  'Actualizar tus datos cuando hayan cambiado.',
  'Rectificar los datos que estén errados.',
  'Revocar tu autorización y pedir que borremos tu información.',
  'Pedir la revisión humana de la decisión sobre tu postulación.',
]
const h2 = 'text-xl font-semibold'

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
    <article className="max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">Cómo evaluamos tu hoja de vida</h1>

      <section aria-labelledby="h-que" className="space-y-3">
        <h2 id="h-que" className={h2}>Qué miramos</h2>
        <p>
          {vacanteId && vacante ? `Para la vacante ${vacante.titulo}` : 'En general'}, evaluamos cinco criterios. El
          porcentaje indica cuánto pesa cada uno en el puntaje final.
        </p>
        <ul aria-label="Criterios de evaluación" className="space-y-2">
          {(Object.keys(ETIQUETA) as NombreCriterio[]).map((c) => (
            <li key={c} className="rounded border border-slate-200 bg-white p-3">
              <strong>{ETIQUETA[c]}</strong> <span className="text-slate-700">({Math.round(pesos[c] * 100)} %)</span>
              <p className="text-sm">{DESCRIPCION[c]}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="h-quien" className="space-y-3">
        <h2 id="h-quien" className={h2}>Quién decide</h2>
        <p>La IA solo extrae información y sugiere un resultado a partir de tu hoja de vida. Nunca rechaza a nadie por sí sola.</p>
        <p>Una persona decide: el equipo de selección revisa la explicación y toma la decisión final antes de escribirte.</p>
      </section>

      <section aria-labelledby="h-datos" className="space-y-3">
        <h2 id="h-datos" className={h2}>Lo que la IA no ve</h2>
        <p>
          Tu nombre, género, edad y origen se ocultan antes de que la IA lea tu hoja de vida, para que esos datos no
          influyan en la sugerencia.
        </p>
      </section>

      <section aria-labelledby="h-derechos" className="space-y-3">
        <h2 id="h-derechos" className={h2}>Tus derechos</h2>
        <p>Según la Ley 1581 de 2012 de protección de datos personales, puedes:</p>
        <ul aria-label="Tus derechos" className="list-inside list-disc">
          {DERECHOS.map((d) => <li key={d}>{d}</li>)}
        </ul>
        <p>
          Para ejercerlos escríbenos a{' '}
          <a href={`mailto:${CORREO}`} className="text-indigo-800 underline">{CORREO}</a> indicando tu nombre y la
          vacante a la que te postulaste.
        </p>
      </section>
    </article>
  )
}
