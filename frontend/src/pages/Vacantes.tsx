import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getVacantes, type Vacante } from '../api'

const Lista = ({ titulo, items }: { titulo: string; items: string[] }) => (
  <div>
    <h3 className="text-sm font-semibold text-slate-700">{titulo}</h3>
    <ul className="mt-1 flex flex-wrap gap-2">
      {items.map((i) => (
        <li key={i} className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-800">
          {i}
        </li>
      ))}
    </ul>
  </div>
)

export function Vacantes() {
  const [vacantes, setVacantes] = useState<Vacante[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    getVacantes().then(setVacantes, () => setError(true))
  }, [])

  if (error) return <p role="alert" className="text-red-700">No pudimos cargar las vacantes. Intenta de nuevo más tarde.</p>
  if (!vacantes) return <p role="status">Cargando vacantes…</p>
  if (vacantes.length === 0) return <p>No hay vacantes abiertas por ahora.</p>

  return (
    <section>
      <h1 className="text-2xl font-bold text-slate-900">Vacantes abiertas</h1>
      <ul className="mt-6 space-y-4">
        {vacantes.map((v) => (
          <li key={v.id} className="space-y-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold">{v.titulo}</h2>
            <Lista titulo="Requisitos obligatorios" items={v.requisitos_obligatorios} />
            <Lista titulo="Deseables" items={v.deseables} />
            <Link
              to={`/aplicar/${v.id}`}
              className="inline-block rounded bg-indigo-700 px-4 py-2 font-medium text-white hover:bg-indigo-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700"
            >
              Aplicar<span className="sr-only"> a {v.titulo}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
