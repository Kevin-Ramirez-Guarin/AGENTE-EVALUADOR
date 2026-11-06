import { beforeEach, describe, expect, it, vi } from 'vitest'
import { decidir, enviarPostulacion, getEvaluacion, getEvaluaciones, getVacante, getVacantes } from './api'

describe('api con mocks', () => {
  beforeEach(() => vi.stubEnv('VITE_USE_MOCKS', 'true'))

  it('lista las vacantes del ejemplo de api.md', async () => {
    const v = await getVacantes()
    expect(v[0].id).toBe('backend-jr')
    expect(v[0].requisitos_obligatorios).toEqual(['Python', 'SQL', 'Git'])
  })

  it('getVacante falla con 404 si no existe', async () => {
    await expect(getVacante('nada')).rejects.toMatchObject({ status: 404 })
  })

  it('enviarPostulacion devuelve el 201 del ejemplo', async () => {
    const r = await enviarPostulacion({
      vacante_id: 'backend-jr',
      nombre: 'A',
      email: 'a@b.co',
      pdf: new File(['x'], 'a.pdf', { type: 'application/pdf' }),
      consentimiento: true,
    })
    expect(r).toEqual({ evaluacion_id: 12, estado: 'pendiente_revision' })
  })

  it('lista evaluaciones filtrando por vacante y paginando', async () => {
    const todas = await getEvaluaciones()
    expect(todas.length).toBeGreaterThan(1)
    expect(todas[0].puntaje_total).toBeGreaterThanOrEqual(todas[1].puntaje_total)
    expect(await getEvaluaciones({ vacante_id: 'nada' })).toEqual([])
    expect(await getEvaluaciones({ limit: 1, offset: 0 })).toHaveLength(1)
  })

  it('getEvaluacion trae criterios con evidencias y 404 si no existe', async () => {
    const e = await getEvaluacion(12)
    expect(e.resultado.criterios?.[0].evidencias.length).toBeGreaterThan(0)
    await expect(getEvaluacion(999)).rejects.toMatchObject({ status: 404 })
  })

  it('decidir devuelve la entrevista con Meet para ENTREVISTA y null si no', async () => {
    const ok = await decidir(12, { veredicto: 'ENTREVISTA', reclutador: 'ana' })
    expect(ok).toMatchObject({ estado: 'decidida', entrevista: { meet_link: expect.stringContaining('meet.google.com') } })
    const no = await decidir(12, { veredicto: 'NO_CONTINUA', motivo: 'x', reclutador: 'ana' })
    expect(no.entrevista).toBeNull()
  })
})
