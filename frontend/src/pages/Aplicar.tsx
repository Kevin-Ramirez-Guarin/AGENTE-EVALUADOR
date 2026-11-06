import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, enviarPostulacion, getVacante, type Vacante } from '../api'
import { boton, campoClase, enlace } from '../estilos'
import { BandaTitulo, Campo, IconoAlerta, IconoCheck, IconoVolver } from '../ui'
import { DetallesVacante } from './Vacantes'

const MAX_BYTES = 5 * 1024 * 1024
const contenedor = 'mx-auto max-w-6xl px-4 sm:px-6'

type Errores = Partial<Record<'nombre' | 'email' | 'pdf' | 'consentimiento', string>>
type Estado = 'editando' | 'enviando' | 'exito' | 'error'

const CAMPOS = ['nombre', 'email', 'pdf', 'consentimiento'] as const

const MENSAJES_API: Record<number, string> = {
  413: 'El archivo supera los 5 MB permitidos.',
  415: 'El archivo no es un PDF válido.',
  422: 'Revisa tus datos y la autorización de tratamiento de datos.',
  404: 'Esta vacante ya no existe.',
}

const mensajeDe = (err: unknown) =>
  (err instanceof ApiError && MENSAJES_API[err.status]) || 'No pudimos enviar tu postulación. Intenta de nuevo.'

function validar(nombre: string, email: string, pdf: File | null, consentimiento: boolean): Errores {
  const e: Errores = {}
  if (!nombre.trim()) e.nombre = 'Escribe tu nombre.'
  if (!/^\S+@\S+\.\S+$/.test(email)) e.email = 'Escribe un correo válido.'
  if (!pdf) e.pdf = 'Adjunta tu hoja de vida en PDF.'
  else if (!pdf.name.toLowerCase().endsWith('.pdf') || pdf.type !== 'application/pdf') e.pdf = 'Solo se aceptan archivos PDF.'
  else if (pdf.size > MAX_BYTES) e.pdf = 'El archivo supera los 5 MB permitidos.'
  if (!consentimiento) e.consentimiento = 'Debes dar tu autorización para poder postularte.'
  return e
}

const Requisitos = ({ titulo, items }: { titulo: string; items: string[] }) =>
  items.length === 0 ? null : (
    <div>
      <h3 className="font-semibold text-selva-900">{titulo}</h3>
      <ul className="mt-2 space-y-1.5">
        {items.map((i) => (
          <li key={i} className="flex items-start gap-2 text-niebla-700">
            <span aria-hidden="true" className="mt-2.5 size-1.5 shrink-0 rounded-full bg-caribe-500" />
            {i}
          </li>
        ))}
      </ul>
    </div>
  )

function SobreElCargo({ v }: { v: Vacante }) {
  const idiomas = (v.idiomas ?? []).map((i) => `${i.idioma} ${i.nivel}`)
  const otros = [
    ...(v.experiencia_min_anios != null ? [`Experiencia mínima: ${v.experiencia_min_anios} ${v.experiencia_min_anios === 1 ? 'año' : 'años'}`] : []),
    ...(idiomas.length ? [`Idiomas: ${idiomas.join(', ')}`] : []),
  ]
  return (
    <section aria-labelledby="h-cargo" className="space-y-8">
      <h2 id="h-cargo" className="text-2xl font-semibold text-selva-900">Sobre el cargo</h2>
      {v.descripcion?.trim() && <p className="max-w-[65ch] text-lg leading-relaxed text-niebla-700">{v.descripcion}</p>}
      <div className="grid gap-8 sm:grid-cols-2">
        <Requisitos titulo="Lo que necesitas" items={v.requisitos_obligatorios ?? []} />
        <Requisitos titulo="Suma si tienes" items={v.deseables ?? []} />
        <Requisitos titulo="Cómo trabajas" items={v.blandas ?? []} />
        <Requisitos titulo="También pedimos" items={otros} />
      </div>
    </section>
  )
}

function Exito({ titulo }: { titulo: string }) {
  const ref = useRef<HTMLDivElement>(null)
  // Lleva el foco al mensaje para que teclado y lector de pantalla lo encuentren de inmediato.
  useEffect(() => {
    ref.current?.focus()
  }, [])
  return (
    <div className={`${contenedor} py-16 sm:py-24`}>
      <div ref={ref} tabIndex={-1} role="status" className="mx-auto max-w-xl rounded-2xl bg-white p-8 text-center shadow-elevada ring-1 ring-niebla-200 focus-visible:outline-none sm:p-12">
        <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-caribe-50 text-caribe-700 ring-8 ring-caribe-50/60">
          <IconoCheck className="size-7" />
        </span>
        <h1 className="mt-6 text-titulo font-semibold text-selva-900">Recibimos tu postulación</h1>
        <p className="mt-4 leading-relaxed text-niebla-700">
          Gracias por postularte a {titulo}. Una persona de nuestro equipo revisará tu hoja de vida y te escribiremos al
          correo que indicaste.
        </p>
        <Link to="/vacantes" className={`${boton('secundario')} mt-8`}>Ver otras vacantes</Link>
      </div>
    </div>
  )
}

export function Aplicar() {
  const { id = '' } = useParams()
  const [vacante, setVacante] = useState<Vacante | null>(null)
  const [fallo, setFallo] = useState(false)
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [pdf, setPdf] = useState<File | null>(null)
  const [consentimiento, setConsentimiento] = useState(false)
  const [errores, setErrores] = useState<Errores>({})
  const [estado, setEstado] = useState<Estado>('editando')
  const [mensajeError, setMensajeError] = useState('')

  useEffect(() => {
    let cancelled = false
    setFallo(false)
    setVacante(null)
    getVacante(id).then(
      (v) => !cancelled && setVacante(v),
      () => !cancelled && setFallo(true),
    )
    return () => {
      cancelled = true
    }
  }, [id])

  async function onSubmit(ev: FormEvent) {
    ev.preventDefault()
    const errs = validar(nombre, email, pdf, consentimiento)
    setErrores(errs)
    const primero = CAMPOS.find((c) => errs[c])
    if (primero || !pdf) {
      if (primero) document.getElementById(primero)?.focus()
      return
    }
    setEstado('enviando')
    try {
      await enviarPostulacion({ vacante_id: id, nombre: nombre.trim(), email: email.trim(), pdf, consentimiento })
      setEstado('exito')
    } catch (err) {
      setMensajeError(mensajeDe(err))
      setEstado('error')
    }
  }

  if (fallo)
    return (
      <div className={`${contenedor} py-16`}>
        <p role="alert" className="rounded-lg bg-red-50 p-4 text-red-800 ring-1 ring-red-200">
          No encontramos esta vacante. <Link className="font-semibold underline" to="/vacantes">Ver vacantes</Link>
        </p>
      </div>
    )
  if (!vacante) return <p className={`${contenedor} py-16 text-niebla-600`}>Cargando…</p>
  if (estado === 'exito') return <Exito titulo={vacante.titulo} />

  const d = (campo: keyof Errores) => (errores[campo] ? { 'aria-invalid': true, 'aria-describedby': `${campo}-error` } : {})

  return (
    <>
      <BandaTitulo
        titulo={vacante.titulo}
        className="pb-10 lg:pb-28"
        antes={
          <Link to="/vacantes" className="-ml-1 inline-flex items-center gap-1 rounded-md py-1 pr-2 text-sm font-medium text-caribe-100 hover:text-white">
            <IconoVolver className="size-4" />
            Todas las vacantes
          </Link>
        }
      >
        <DetallesVacante v={vacante} claro />
        <a href="#h-postulate" className={`${boton('acento')} lg:hidden`}>Ir al formulario</a>
      </BandaTitulo>

      <div className={`${contenedor} grid gap-12 py-10 lg:grid-cols-[1fr_27rem] lg:gap-16`}>
        <div className="lg:pt-6">
          <SobreElCargo v={vacante} />
        </div>

        <section aria-labelledby="h-postulate" className="scroll-mt-4 rounded-2xl bg-white p-6 shadow-elevada ring-1 ring-niebla-200 sm:p-8 lg:-mt-24 lg:self-start">
          <h2 id="h-postulate" className="text-2xl font-semibold text-selva-900">Postúlate</h2>
          <p className="mt-1 text-sm text-niebla-600">Te toma unos dos minutos. Todos los campos son obligatorios.</p>
          <form onSubmit={onSubmit} noValidate className="mt-6 space-y-5">
            <Campo id="nombre" label="Nombre completo" error={errores.nombre}>
              <input id="nombre" className={campoClase} required autoComplete="name" value={nombre} onChange={(e) => setNombre(e.target.value)} {...d('nombre')} />
            </Campo>
            <Campo id="email" label="Correo electrónico" error={errores.email}>
              <input id="email" type="email" className={campoClase} required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} {...d('email')} />
            </Campo>
            <Campo id="pdf" label="Hoja de vida (PDF, máximo 5 MB)" error={errores.pdf}>
              <input
                id="pdf"
                type="file"
                accept=".pdf,application/pdf"
                className={`${campoClase} cursor-pointer border-dashed py-3 text-sm file:mr-3 file:cursor-pointer file:rounded-full file:border-0 file:bg-caribe-50 file:px-4 file:py-2 file:font-semibold file:text-caribe-800 hover:file:bg-caribe-100`}
                required
                onChange={(e) => setPdf(e.target.files?.[0] ?? null)}
                {...d('pdf')}
              />
            </Campo>

            <div className={`rounded-lg p-4 ring-1 ${errores.consentimiento ? 'bg-red-50/60 ring-red-300' : 'bg-niebla-50 ring-niebla-200'}`}>
              <div className="flex items-start gap-3">
                <input
                  id="consentimiento"
                  type="checkbox"
                  required
                  checked={consentimiento}
                  onChange={(e) => setConsentimiento(e.target.checked)}
                  className="mt-0.5 size-5 shrink-0 cursor-pointer accent-caribe-700"
                  aria-invalid={errores.consentimiento ? true : undefined}
                  aria-describedby={`consentimiento-info${errores.consentimiento ? ' consentimiento-error' : ''}`}
                />
                <label htmlFor="consentimiento" className="cursor-pointer font-semibold text-niebla-900">
                  Autorizo el tratamiento de mis datos (Ley 1581 de 2012)
                </label>
              </div>
              <p id="consentimiento-info" className="mt-2 text-sm leading-relaxed text-niebla-700">
                Usaremos tus datos solo para evaluar esta postulación. Una inteligencia artificial ayuda a analizar tu hoja de
                vida, pero la decisión final la toma una persona de nuestro equipo.
              </p>
              <p className="mt-2 text-sm leading-relaxed text-niebla-700">
                Lee la <Link to="/privacidad" className={enlace}>política de privacidad</Link> y conoce{' '}
                <Link to={`/como-evaluamos?vacante=${encodeURIComponent(id)}`} className={enlace}>cómo evaluamos tu hoja de vida</Link>.
              </p>
              {errores.consentimiento && (
                <p id="consentimiento-error" className="mt-2 flex items-start gap-1.5 text-sm font-medium text-red-700">
                  <IconoAlerta className="mt-0.5 size-4 shrink-0" />
                  {errores.consentimiento}
                </p>
              )}
            </div>

            {estado === 'error' && (
              <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm font-medium text-red-800 ring-1 ring-red-200">{mensajeError}</p>
            )}
            <button type="submit" disabled={estado === 'enviando'} className={`${boton('primario')} w-full`}>
              {estado === 'enviando' ? 'Enviando…' : 'Enviar postulación'}
            </button>
          </form>
        </section>
      </div>
    </>
  )
}
