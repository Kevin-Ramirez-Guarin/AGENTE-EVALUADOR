import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, enviarPostulacion, getVacante, type Vacante } from '../api'

const MAX_BYTES = 5 * 1024 * 1024
const input =
  'mt-1 block w-full rounded border border-slate-400 px-3 py-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700 aria-[invalid=true]:border-red-700'

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

function Campo({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="font-medium">{label}</label>
      {children}
      {error && <p id={`${id}-error`} className="mt-1 text-sm text-red-700">{error}</p>}
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

  if (fallo) return <p role="alert" className="text-red-700">No encontramos esta vacante. <Link className="underline" to="/vacantes">Ver vacantes</Link></p>
  if (!vacante) return <p>Cargando…</p>
  if (estado === 'exito')
    return (
      <div role="status" className="rounded-lg border border-green-300 bg-green-50 p-5">
        <h1 className="text-xl font-bold">Recibimos tu postulación</h1>
        <p className="mt-2">Gracias por postularte a {vacante.titulo}. Una persona de nuestro equipo revisará tu hoja de vida y te escribiremos al correo que indicaste.</p>
      </div>
    )

  const d = (campo: keyof Errores) => (errores[campo] ? { 'aria-invalid': true, 'aria-describedby': `${campo}-error` } : {})

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      <h1 className="text-2xl font-bold">{vacante.titulo}</h1>
      <Campo id="nombre" label="Nombre completo" error={errores.nombre}>
        <input id="nombre" className={input} required autoComplete="name" value={nombre} onChange={(e) => setNombre(e.target.value)} {...d('nombre')} />
      </Campo>
      <Campo id="email" label="Correo electrónico" error={errores.email}>
        <input id="email" type="email" className={input} required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} {...d('email')} />
      </Campo>
      <Campo id="pdf" label="Hoja de vida (PDF, máximo 5 MB)" error={errores.pdf}>
        <input id="pdf" type="file" accept=".pdf,application/pdf" className={input} required onChange={(e) => setPdf(e.target.files?.[0] ?? null)} {...d('pdf')} />
      </Campo>
      <div>
        <div className="flex items-start gap-2">
          <input
            id="consentimiento"
            type="checkbox"
            required
            checked={consentimiento}
            onChange={(e) => setConsentimiento(e.target.checked)}
            className="mt-1 size-5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700"
            aria-invalid={errores.consentimiento ? true : undefined}
            aria-describedby={`consentimiento-info${errores.consentimiento ? ' consentimiento-error' : ''}`}
          />
          <label htmlFor="consentimiento" className="font-medium">Autorizo el tratamiento de mis datos (Ley 1581 de 2012)</label>
        </div>
        <p id="consentimiento-info" className="mt-1 text-sm text-slate-700">
          Usaremos tus datos solo para evaluar esta postulación. Una inteligencia artificial ayuda a analizar tu hoja de vida,
          pero la decisión final la toma una persona de nuestro equipo.
        </p>
        <p className="mt-1 text-sm">
          Lee la <Link to="/privacidad" className="text-indigo-700 underline">política de privacidad</Link>.
        </p>
        {errores.consentimiento && <p id="consentimiento-error" className="mt-1 text-sm text-red-700">{errores.consentimiento}</p>}
      </div>
      {estado === 'error' && <p role="alert" className="text-red-700">{mensajeError}</p>}
      <button
        type="submit"
        disabled={estado === 'enviando'}
        className="rounded bg-indigo-700 px-5 py-2 font-medium text-white hover:bg-indigo-800 disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-700"
      >
        {estado === 'enviando' ? 'Enviando…' : 'Enviar postulación'}
      </button>
    </form>
  )
}
