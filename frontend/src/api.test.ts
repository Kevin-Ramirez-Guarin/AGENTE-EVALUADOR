import { beforeEach, describe, expect, it, vi } from 'vitest'
import { enviarPostulacion, getVacante, getVacantes } from './api'

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
})
