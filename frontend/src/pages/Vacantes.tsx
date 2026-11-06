import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getVacantes, type Vacante } from '../api'
import { RutaMapa } from '../RutaMapa'
import { boton, enlace } from '../estilos'
import { IconoEquipo, IconoModalidad, IconoUbicacion } from '../ui'

const contenedor = 'mx-auto max-w-6xl px-4 sm:px-6'

const RAZONES = [
  {
    titulo: 'Temporada alta',
    texto: 'Diciembre y enero son nuestros meses más intensos. Buscamos gente que aprenda rápido y cuide a cada viajero de principio a fin.',
    color: 'border-mango-400',
  },
  {
    titulo: 'Nueva app de reservas',
    texto: 'Estamos construyendo la app con la que los viajeros reservan, pagan en línea y hablan con su guía. Hay espacio para proponer.',
    color: 'border-caribe-500',
  },
  {
    titulo: 'Nuevos destinos',
    texto: 'Vamos a llevar Giveaway a más regiones del país, siempre de la mano de guías locales que conocen su tierra.',
    color: 'border-cafetal-600',
  },
]

const PASOS = [
  { titulo: 'Te postulas', texto: 'Eliges la vacante, subes tu hoja de vida en PDF y autorizas el tratamiento de tus datos.' },
  {
    titulo: 'La IA lee tu hoja de vida sin saber quién eres',
    texto: 'Antes de analizarla quitamos tu nombre, tu contacto y otros datos personales. La IA compara tu experiencia con lo que pide el cargo y explica su recomendación.',
  },
  {
    titulo: 'Una persona de Talento decide',
    texto: 'La IA recomienda, una persona del equipo de Talento decide. Revisa la explicación y puede cambiar la recomendación.',
  },
  { titulo: 'Te escribimos', texto: 'Recibes la respuesta en tu correo. Si sigues en el proceso, ahí mismo llega la invitación a la entrevista.' },
]

const Chips = ({ titulo, items, estilo }: { titulo: string; items: string[]; estilo: string }) =>
  items.length === 0 ? null : (
    <div>
      <h4 className="text-sm font-semibold text-niebla-700">{titulo}</h4>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {items.map((i) => (
          <li key={i} className={`rounded-full px-3 py-1 text-sm ${estilo}`}>{i}</li>
        ))}
      </ul>
    </div>
  )

// Equipo, ubicación y modalidad son opcionales: solo se listan los que llegan con texto.
export function DetallesVacante({ v, claro = false }: { v: Vacante; claro?: boolean }) {
  const detalles = [
    { texto: v.equipo, Icono: IconoEquipo },
    { texto: v.ubicacion, Icono: IconoUbicacion },
    { texto: v.modalidad, Icono: IconoModalidad },
  ].filter((d) => d.texto?.trim())
  if (detalles.length === 0) return null
  return (
    <ul aria-label="Detalles de la vacante" className={`flex flex-wrap gap-x-5 gap-y-1.5 text-sm ${claro ? 'text-caribe-100' : 'text-niebla-600'}`}>
      {detalles.map(({ texto, Icono }) => (
        <li key={texto} className="flex items-center gap-1.5">
          <Icono className={`size-4 shrink-0 ${claro ? 'text-caribe-300' : 'text-caribe-700'}`} />
          {texto}
        </li>
      ))}
    </ul>
  )
}

function TarjetaVacante({ v }: { v: Vacante }) {
  return (
    <article className="grid gap-6 rounded-xl bg-white p-6 shadow-tarjeta ring-1 ring-niebla-200 sm:grid-cols-[1fr_auto] sm:p-8">
      <div className="space-y-3">
        <h3 className="text-xl font-semibold tracking-[-0.01em] text-selva-900 sm:text-2xl">{v.titulo}</h3>
        <DetallesVacante v={v} />
        {v.descripcion?.trim() && <p className="max-w-[68ch] leading-relaxed text-niebla-700">{v.descripcion}</p>}
      </div>
      <div className="grid gap-5 sm:col-span-2 sm:grid-cols-2">
        <Chips titulo="Requisitos obligatorios" items={v.requisitos_obligatorios ?? []} estilo="bg-caribe-50 font-medium text-caribe-800 ring-1 ring-inset ring-caribe-200" />
        <Chips titulo="Deseables" items={v.deseables ?? []} estilo="border border-dashed border-niebla-500 text-niebla-700" />
      </div>
      <Link to={`/aplicar/${v.id}`} className={`${boton('primario')} order-last sm:order-none sm:col-start-2 sm:row-start-1 sm:self-start`}>
        Aplicar<span className="sr-only"> a {v.titulo}</span>
      </Link>
    </article>
  )
}

function ListaVacantes() {
  const [vacantes, setVacantes] = useState<Vacante[] | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    getVacantes().then(setVacantes, () => setError(true))
  }, [])

  if (error) return <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-800 ring-1 ring-red-200">No pudimos cargar las vacantes. Intenta de nuevo más tarde.</p>
  if (!vacantes) return <p role="status" className="rounded-lg bg-white p-6 text-niebla-600 ring-1 ring-niebla-200">Cargando vacantes…</p>
  if (vacantes.length === 0)
    return <p className="rounded-lg bg-white p-6 text-niebla-700 ring-1 ring-niebla-200">No hay vacantes abiertas por ahora. Vuelve pronto: en temporada alta abrimos cargos nuevos.</p>

  return (
    <>
      <p className="-mt-6 mb-8 text-niebla-600">{vacantes.length === 1 ? '1 cargo' : `${vacantes.length} cargos`} con inicio inmediato.</p>
      <ul className="space-y-5">
        {vacantes.map((v) => <li key={v.id}><TarjetaVacante v={v} /></li>)}
      </ul>
    </>
  )
}

export function Vacantes() {
  return (
    <>
      <section data-tono="oscuro" aria-labelledby="h-hero" className="overflow-hidden bg-selva-900 text-white">
        <div className={`${contenedor} grid items-center gap-10 pt-10 pb-16 lg:grid-cols-[1.35fr_1fr] lg:gap-16 lg:pt-14 lg:pb-24`}>
          <div className="space-y-6">
            <h1 id="h-hero" className="text-hero font-semibold">
              Ayúdanos a que más viajeros descubran Colombia con quien mejor la conoce.
            </h1>
            <p className="max-w-xl text-lg leading-relaxed text-caribe-100">
              Somos Giveaway, la plataforma colombiana para descubrir y reservar tours y experiencias con guías locales
              certificados. Somos unas 60 personas en Medellín y estamos creciendo para la temporada alta.
            </p>
            <a href="#vacantes" className={boton('acento')}>Ver vacantes</a>
          </div>
          <div className="mx-auto w-full max-w-sm lg:max-w-md">
            <RutaMapa />
          </div>
        </div>
      </section>

      <section aria-labelledby="h-por-que" className="py-16 sm:py-20">
        <div className={`${contenedor} grid gap-10 lg:grid-cols-[2fr_3fr] lg:gap-16`}>
          <div className="space-y-4">
            <h2 id="h-por-que" className="text-titulo font-semibold text-selva-900">Por qué Giveaway</h2>
            <p className="leading-relaxed text-niebla-700">
              Cada experiencia la guía alguien que conoce su tierra: Cartagena, Medellín y la Comuna 13, el Eje Cafetero,
              el Parque Tayrona, Bogotá y Guatapé. Detrás hay un equipo que construye la web y la app de reservas, los
              pagos en línea y el soporte a viajeros 24/7.
            </p>
          </div>
          <ul className="grid gap-8 sm:grid-cols-3 sm:gap-6">
            {RAZONES.map((r) => (
              <li key={r.titulo} className={`border-t-4 pt-4 ${r.color}`}>
                <h3 className="text-lg font-semibold text-selva-900">{r.titulo}</h3>
                <p className="mt-2 leading-relaxed text-niebla-700">{r.texto}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="vacantes" aria-labelledby="h-vacantes" className="scroll-mt-4 bg-niebla-100 py-16 sm:py-20">
        <div className={contenedor}>
          <h2 id="h-vacantes" className="mb-8 text-titulo font-semibold text-selva-900">Vacantes abiertas</h2>
          <ListaVacantes />
        </div>
      </section>

      <section aria-labelledby="h-proceso" className="py-16 sm:py-20">
        <div className={contenedor}>
          <h2 id="h-proceso" className="text-titulo font-semibold text-selva-900">Cómo es el proceso</h2>
          <ol className="mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
            {PASOS.map((p, i) => (
              <li key={p.titulo} className="relative">
                <span aria-hidden="true" className="font-display flex size-10 items-center justify-center rounded-full bg-selva-900 text-lg font-bold text-mango-300">
                  {i + 1}
                </span>
                <h3 className="mt-4 text-lg font-semibold text-selva-900">{p.titulo}</h3>
                <p className="mt-2 leading-relaxed text-niebla-700">{p.texto}</p>
              </li>
            ))}
          </ol>
          <p className="mt-10 text-niebla-700">
            ¿Quieres el detalle? <Link to="/como-evaluamos" className={enlace}>Lee cómo evaluamos tu hoja de vida</Link>.
          </p>
        </div>
      </section>
    </>
  )
}
