import type { NombreCriterio } from './api'

export const ETIQUETA: Record<NombreCriterio, string> = {
  tecnico: 'Técnico',
  experiencia: 'Experiencia',
  blandas: 'Habilidades blandas',
  educacion: 'Educación',
  idiomas: 'Idiomas',
}

export const DESCRIPCION: Record<NombreCriterio, string> = {
  tecnico: 'Las herramientas y tecnologías que pide la vacante, solo si tu hoja de vida muestra evidencia de haberlas usado.',
  experiencia: 'Los años de experiencia que tienes frente al mínimo que pide la vacante.',
  blandas: 'Habilidades como el trabajo en equipo o el aprendizaje, cuando hay ejemplos concretos en tu hoja de vida.',
  educacion: 'Tu nivel de estudios frente al nivel mínimo de la vacante.',
  idiomas: 'Los idiomas y niveles que pide la vacante.',
}

// Pesos genéricos de PLAN §5; cada vacante puede definir los suyos.
export const PESOS_GENERICOS: Record<NombreCriterio, number> = {
  tecnico: 0.45,
  experiencia: 0.25,
  blandas: 0.15,
  educacion: 0.1,
  idiomas: 0.05,
}
