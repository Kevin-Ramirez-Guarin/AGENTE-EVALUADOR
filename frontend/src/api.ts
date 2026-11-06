// Cliente de la API. Tipos y mocks siguen exactamente docs/api.md.

export interface Idioma {
  idioma: string
  nivel: string
}

export interface Vacante {
  id: string
  titulo: string
  requisitos_obligatorios: string[]
  deseables: string[]
  blandas: string[]
  experiencia_min_anios: number
  nivel_educativo_min: string
  idiomas: Idioma[]
  pesos: { tecnico: number; experiencia: number; blandas: number; educacion: number; idiomas: number }
}

export interface PostulacionInput {
  vacante_id: string
  nombre: string
  email: string
  pdf: File
  consentimiento: boolean
}

export interface PostulacionCreada {
  evaluacion_id: number
  estado: string
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const MOCK_VACANTES: Vacante[] = [
  {
    id: 'backend-jr',
    titulo: 'Desarrollador/a Backend Jr (Python)',
    requisitos_obligatorios: ['Python', 'SQL', 'Git'],
    deseables: ['FastAPI/Django', 'Docker', 'Testing'],
    blandas: ['Trabajo en equipo', 'Aprendizaje'],
    experiencia_min_anios: 1,
    nivel_educativo_min: 'tecnologo',
    idiomas: [{ idioma: 'inglés', nivel: 'A2' }],
    pesos: { tecnico: 0.45, experiencia: 0.25, blandas: 0.15, educacion: 0.1, idiomas: 0.05 },
  },
]
const MOCK_POSTULACION: PostulacionCreada = { evaluacion_id: 12, estado: 'pendiente_revision' }

const useMocks = () => import.meta.env.VITE_USE_MOCKS === 'true'
const baseUrl = () => import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export async function getVacantes(): Promise<Vacante[]> {
  if (useMocks()) return MOCK_VACANTES
  return request('/vacantes')
}

export async function getVacante(id: string): Promise<Vacante> {
  if (useMocks()) {
    const v = MOCK_VACANTES.find((m) => m.id === id)
    if (!v) throw new ApiError(404, 'Vacante no encontrada')
    return v
  }
  return request(`/vacantes/${encodeURIComponent(id)}`)
}

export async function enviarPostulacion(input: PostulacionInput): Promise<PostulacionCreada> {
  if (useMocks()) return MOCK_POSTULACION
  const form = new FormData()
  form.append('vacante_id', input.vacante_id)
  form.append('nombre', input.nombre)
  form.append('email', input.email)
  form.append('pdf', input.pdf)
  form.append('consentimiento', String(input.consentimiento))
  return request('/postulaciones', { method: 'POST', body: form })
}
