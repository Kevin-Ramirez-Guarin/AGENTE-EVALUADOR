import { describe, expect, it } from 'vitest'
import { bandaPuntaje, VEREDICTOS } from './estados'

describe('bandaPuntaje', () => {
  it.each([
    [100, 'alta'],
    [75, 'alta'],
    [74.9, 'media'],
    [55, 'media'],
    [54.9, 'baja'],
    [0, 'baja'],
  ])('%d cae en la banda %s (umbrales de PLAN §5)', (puntaje, banda) => {
    expect(bandaPuntaje(puntaje)).toBe(banda)
  })
})

describe('VEREDICTOS', () => {
  it('da un texto legible para cada veredicto de la API', () => {
    expect(VEREDICTOS.ENTREVISTA.texto).toBe('Entrevista')
    expect(VEREDICTOS.REVISION_HUMANA.texto).toBe('Revisión humana')
    expect(VEREDICTOS.NO_CONTINUA.texto).toBe('No continúa')
  })
})
