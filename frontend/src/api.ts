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
  // Opcionales: un backend anterior puede no enviarlos o enviarlos vacíos.
  descripcion?: string
  equipo?: string
  ubicacion?: string
  modalidad?: string
}

export interface PostulacionInput {
  vacante_id: string
  nombre: string
  email: string
  pdf: File
  consentimiento: boolean
}

export type EstadoEvaluacion = 'en_evaluacion' | 'pendiente_revision' | 'decidida' | 'error_evaluacion'

export interface PostulacionCreada {
  evaluacion_id: number
  estado: EstadoEvaluacion
}

export type Veredicto = 'ENTREVISTA' | 'REVISION_HUMANA' | 'NO_CONTINUA'
export type NombreCriterio = 'tecnico' | 'experiencia' | 'blandas' | 'educacion' | 'idiomas'

export interface CriterioDetalle {
  criterio: NombreCriterio
  puntaje: number // 0-100
  peso: number // 0-1
  cumplidos: string[]
  faltantes: string[]
  evidencias: string[]
  nota: string
}

export interface Habilidad {
  nombre: string
  nivel: string
  evidencia: string
}

export interface Perfil {
  habilidades_tecnicas: Habilidad[]
  habilidades_blandas: Habilidad[]
  anios_experiencia: number
  nivel_educativo: string
  idiomas: Idioma[]
  fortalezas: string[]
  debilidades: string[]
  resumen: string
}

export interface Resultado {
  puntaje_total: number
  puntajes_por_criterio: Record<NombreCriterio, number>
  criterios?: CriterioDetalle[]
  veredicto_sugerido: Veredicto
  cumple_obligatorios: boolean
  explicacion: string
  mejor_vacante_alternativa: string | null
}

export interface EvaluacionResumen {
  id: number
  vacante_id: string
  candidato: string
  puntaje_total: number | null
  veredicto_sugerido: Veredicto | null
  veredicto_final: Veredicto | null
  estado: EstadoEvaluacion
}

export interface EvaluacionDetalle {
  id: number
  vacante_id: string
  candidato: string
  perfil: Perfil | null
  resultado: Resultado | null
  veredicto_final: Veredicto | null
  estado: EstadoEvaluacion
  error: string | null
}

export interface DecisionInput {
  veredicto: Veredicto
  motivo?: string
  reclutador: string
}

export interface DecisionRespuesta {
  id: number
  veredicto_final: Veredicto
  estado: string
  entrevista: { inicio: string; meet_link: string } | null
}

export interface FiltroEvaluaciones {
  vacante_id?: string
  limit?: number
  offset?: number
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
    equipo: 'Producto y Tecnología',
    ubicacion: 'Medellín, Colombia',
    modalidad: 'Híbrido · Medellín',
    descripcion: 'Construyes y mantienes el motor de reservas y disponibilidad de tours: las APIs que conectan los cupos de los guías locales con la web y la nueva app.',
  },
]
const MOCK_POSTULACION: PostulacionCreada = { evaluacion_id: 12, estado: 'en_evaluacion' }

const MOCK_DETALLE_12: EvaluacionDetalle = {
  id: 12,
  vacante_id: 'backend-jr',
  candidato: 'Ana Pérez',
  perfil: {
    habilidades_tecnicas: [
      { nombre: 'Python', nivel: 'avanzado', evidencia: '2 años desarrollando APIs en Python' },
      { nombre: 'SQL', nivel: 'intermedio', evidencia: 'Consultas y modelado en PostgreSQL' },
    ],
    habilidades_blandas: [{ nombre: 'Trabajo en equipo', nivel: 'intermedio', evidencia: 'Lideró dailies en un equipo de 5 personas' }],
    anios_experiencia: 2,
    nivel_educativo: 'tecnologo',
    idiomas: [{ idioma: 'inglés', nivel: 'B1' }],
    fortalezas: ['Dominio de Python'],
    debilidades: ['Poca experiencia con Docker'],
    resumen: 'Desarrolladora backend con 2 años de experiencia.',
  },
  resultado: {
    puntaje_total: 82.5,
    puntajes_por_criterio: { tecnico: 88, experiencia: 80, blandas: 70, educacion: 100, idiomas: 100 },
    criterios: [
      { criterio: 'tecnico', puntaje: 88, peso: 0.45, cumplidos: ['Python', 'SQL', 'Git'], faltantes: ['Docker'], evidencias: ['2 años desarrollando APIs en Python'], nota: 'Cumple los obligatorios; falta Docker (deseable).' },
      { criterio: 'experiencia', puntaje: 80, peso: 0.25, cumplidos: ['2 años (mínimo 1)'], faltantes: [], evidencias: ['Backend en Ruta Norte Software, 2022-2024'], nota: 'Supera el mínimo.' },
      { criterio: 'blandas', puntaje: 70, peso: 0.15, cumplidos: ['Trabajo en equipo'], faltantes: ['Aprendizaje'], evidencias: ['Lideró dailies en un equipo de 5 personas'], nota: 'Evidencia parcial.' },
      { criterio: 'educacion', puntaje: 100, peso: 0.1, cumplidos: ['Tecnólogo'], faltantes: [], evidencias: ['Tecnólogo en Desarrollo de Software'], nota: 'Cumple el nivel mínimo.' },
      { criterio: 'idiomas', puntaje: 100, peso: 0.05, cumplidos: ['Inglés B1 (mínimo A2)'], faltantes: [], evidencias: ['Certificado B1'], nota: 'Supera el nivel pedido.' },
    ],
    veredicto_sugerido: 'ENTREVISTA',
    cumple_obligatorios: true,
    explicacion: 'Cumple los 3 requisitos obligatorios con evidencia en la HV.',
    mejor_vacante_alternativa: null,
  },
  veredicto_final: null,
  estado: 'pendiente_revision',
  error: null,
}
// Sin `criterios`: ejercita el respaldo a puntajes_por_criterio.
const MOCK_DETALLE_13: EvaluacionDetalle = {
  ...MOCK_DETALLE_12,
  id: 13,
  candidato: 'Luis Gómez',
  resultado: {
    ...MOCK_DETALLE_12.resultado,
    puntaje_total: 41,
    puntajes_por_criterio: { tecnico: 40, experiencia: 30, blandas: 50, educacion: 60, idiomas: 40 },
    criterios: undefined,
    veredicto_sugerido: 'NO_CONTINUA',
    cumple_obligatorios: false,
    explicacion: 'No evidencia SQL ni Git.',
    mejor_vacante_alternativa: 'frontend-jr',
  },
}
const MOCK_DETALLE_14: EvaluacionDetalle = { ...MOCK_DETALLE_12, id: 14, candidato: 'Sara Díaz', perfil: null, resultado: null, estado: 'en_evaluacion' }
const MOCK_DETALLE_15: EvaluacionDetalle = {
  ...MOCK_DETALLE_14,
  id: 15,
  candidato: 'Pedro Ríos',
  estado: 'error_evaluacion',
  error: 'El servicio de IA no respondió a tiempo.',
}
const MOCK_DETALLE_16: EvaluacionDetalle = { ...MOCK_DETALLE_12, id: 16, candidato: 'Marta Ruiz', veredicto_final: 'ENTREVISTA', estado: 'decidida' }
const MOCK_DETALLES = [MOCK_DETALLE_12, MOCK_DETALLE_13, MOCK_DETALLE_16, MOCK_DETALLE_14, MOCK_DETALLE_15]
const MOCK_ENTREVISTA = { inicio: '2026-11-09T10:00:00-05:00', meet_link: 'https://meet.google.com/xxx-xxxx-xxx' }

const mocksActivos = () => import.meta.env.VITE_USE_MOCKS === 'true'
const baseUrl = () => import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl()}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  return (res.status === 202 ? undefined : res.json()) as Promise<T>
}

export async function getVacantes(): Promise<Vacante[]> {
  if (mocksActivos()) return MOCK_VACANTES
  return request('/vacantes')
}

export async function getVacante(id: string): Promise<Vacante> {
  if (mocksActivos()) {
    const v = MOCK_VACANTES.find((m) => m.id === id)
    if (!v) throw new ApiError(404, 'Vacante no encontrada')
    return v
  }
  return request(`/vacantes/${encodeURIComponent(id)}`)
}

export async function enviarPostulacion(input: PostulacionInput): Promise<PostulacionCreada> {
  if (mocksActivos()) return MOCK_POSTULACION
  const form = new FormData()
  form.append('vacante_id', input.vacante_id)
  form.append('nombre', input.nombre)
  form.append('email', input.email)
  form.append('pdf', input.pdf)
  form.append('consentimiento', String(input.consentimiento))
  return request('/postulaciones', { method: 'POST', body: form })
}

export async function getEvaluaciones(f: FiltroEvaluaciones = {}): Promise<EvaluacionResumen[]> {
  if (mocksActivos()) {
    const filas = MOCK_DETALLES.filter((d) => !f.vacante_id || d.vacante_id === f.vacante_id).map((d) => ({
      id: d.id,
      vacante_id: d.vacante_id,
      candidato: d.candidato,
      puntaje_total: d.resultado?.puntaje_total ?? null,
      veredicto_sugerido: d.resultado?.veredicto_sugerido ?? null,
      veredicto_final: d.veredicto_final,
      estado: d.estado,
    }))
    const desde = f.offset ?? 0
    return filas.slice(desde, desde + (f.limit ?? 50))
  }
  const q = new URLSearchParams()
  if (f.vacante_id) q.set('vacante_id', f.vacante_id)
  if (f.limit !== undefined) q.set('limit', String(f.limit))
  if (f.offset !== undefined) q.set('offset', String(f.offset))
  return request(`/evaluaciones?${q}`)
}

export async function getEvaluacion(id: number): Promise<EvaluacionDetalle> {
  if (mocksActivos()) {
    const d = MOCK_DETALLES.find((m) => m.id === id)
    if (!d) throw new ApiError(404, 'Evaluación no encontrada')
    return d
  }
  return request(`/evaluaciones/${id}`)
}

export async function decidir(id: number, input: DecisionInput): Promise<DecisionRespuesta> {
  if (mocksActivos()) {
    return {
      id,
      veredicto_final: input.veredicto,
      estado: 'decidida',
      entrevista: input.veredicto === 'ENTREVISTA' ? MOCK_ENTREVISTA : null,
    }
  }
  return request(`/evaluaciones/${id}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

// 202 si la evaluación está en error_evaluacion; 409 si no.
export async function reintentarEvaluacion(id: number): Promise<void> {
  if (mocksActivos()) {
    if (MOCK_DETALLES.find((m) => m.id === id)?.estado !== 'error_evaluacion') throw new ApiError(409, 'La evaluación no está en error')
    return
  }
  await request(`/evaluaciones/${id}/reintentar`, { method: 'POST' })
}
