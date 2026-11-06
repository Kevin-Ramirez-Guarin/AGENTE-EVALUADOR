import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from '../api'
import { Panel } from './Panel'

vi.mock('../api')

const fila = (o: Partial<api.EvaluacionResumen>): api.EvaluacionResumen => ({
  id: 1,
  vacante_id: 'backend-jr',
  candidato: 'Ana Pérez',
  puntaje_total: 82.5,
  veredicto_sugerido: 'ENTREVISTA',
  veredicto_final: null,
  estado: 'pendiente_revision',
  ...o,
})
const vacantes = [{ id: 'backend-jr', titulo: 'Backend Jr' }, { id: 'frontend-jr', titulo: 'Frontend Jr' }] as api.Vacante[]

const setup = () => {
  render(
    <MemoryRouter>
      <Panel />
    </MemoryRouter>,
  )
  return userEvent.setup()
}

describe('Panel', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(api.getVacantes).mockResolvedValue(vacantes)
    vi.mocked(api.getEvaluaciones).mockResolvedValue([
      fila({ id: 12 }),
      fila({ id: 13, candidato: 'Luis Gómez', puntaje_total: 41, veredicto_sugerido: 'NO_CONTINUA', veredicto_final: 'REVISION_HUMANA', estado: 'decidida' }),
    ])
  })

  it('muestra el aviso de demo y una tabla con encabezados y una fila por evaluación', async () => {
    setup()
    expect(screen.getByText(/demo sin autenticación/i)).toBeInTheDocument()
    const tabla = await screen.findByRole('table')
    for (const h of ['Candidato', 'Vacante', 'Puntaje', 'Sugerido por la IA', 'Decisión final', 'Estado']) {
      expect(within(tabla).getByRole('columnheader', { name: h })).toBeInTheDocument()
    }
    const filas = within(tabla).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(2)
    expect(within(filas[0]).getByRole('link', { name: /ana pérez/i })).toHaveAttribute('href', '/panel/12')
    expect(filas[0]).toHaveTextContent('82.5')
    expect(filas[0]).toHaveTextContent('Backend Jr')
    expect(filas[0]).toHaveTextContent('ENTREVISTA')
    expect(filas[1]).toHaveTextContent('REVISION_HUMANA')
    expect(filas[1]).toHaveTextContent('decidida')
  })

  it('filtra por vacante y vuelve al inicio de la paginación', async () => {
    const user = setup()
    await screen.findByRole('table')
    await user.selectOptions(screen.getByLabelText('Vacante'), 'frontend-jr')
    expect(api.getEvaluaciones).toHaveBeenLastCalledWith({ vacante_id: 'frontend-jr', limit: 10, offset: 0 })
  })

  it('pagina con limit/offset y deshabilita Siguiente en la última página', async () => {
    const user = setup()
    await screen.findByRole('table')
    expect(screen.getByRole('button', { name: /anterior/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /siguiente/i })).toBeDisabled() // 2 filas < limit

    vi.mocked(api.getEvaluaciones).mockResolvedValue(Array.from({ length: 10 }, (_, i) => fila({ id: i + 1 })))
    await user.selectOptions(screen.getByLabelText('Vacante'), 'backend-jr')
    await user.click(await screen.findByRole('button', { name: /siguiente/i }))
    expect(api.getEvaluaciones).toHaveBeenLastCalledWith({ vacante_id: 'backend-jr', limit: 10, offset: 10 })
  })

  it('indica cuando no hay evaluaciones', async () => {
    vi.mocked(api.getEvaluaciones).mockResolvedValue([])
    setup()
    expect(await screen.findByText(/no hay evaluaciones/i)).toBeInTheDocument()
  })

  it('muestra un error si la API falla', async () => {
    vi.mocked(api.getEvaluaciones).mockRejectedValue(new Error('boom'))
    setup()
    expect(await screen.findByRole('alert')).toHaveTextContent(/no pudimos cargar/i)
  })
})
