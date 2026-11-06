import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from '../api'
import { ComoEvaluamos } from './ComoEvaluamos'
import { Privacidad } from './Privacidad'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  getVacante: vi.fn(),
}))

const vacante = {
  id: 'backend-jr',
  titulo: 'Backend Jr',
  pesos: { tecnico: 0.5, experiencia: 0.2, blandas: 0.1, educacion: 0.1, idiomas: 0.1 },
} as api.Vacante

const setup = (url = '/como-evaluamos') =>
  render(
    <MemoryRouter initialEntries={[url]}>
      <ComoEvaluamos />
    </MemoryRouter>,
  )

describe('ComoEvaluamos', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(api.getVacante).mockResolvedValue(vacante)
  })

  it('sin ?vacante= lista los 5 criterios con los pesos genéricos y no llama a la API', () => {
    setup()
    expect(screen.getByRole('heading', { level: 1, name: /cómo evaluamos/i })).toBeInTheDocument()
    const lista = screen.getByRole('list', { name: /criterios/i })
    const items = within(lista).getAllByRole('listitem')
    expect(items).toHaveLength(5)
    const pesos = ['45 %', '25 %', '15 %', '10 %', '5 %']
    items.forEach((li, i) => expect(li).toHaveTextContent(pesos[i]))
    expect(api.getVacante).not.toHaveBeenCalled()
  })

  it('con ?vacante= lee los pesos de esa vacante', async () => {
    setup('/como-evaluamos?vacante=backend-jr')
    expect(await screen.findByText(/backend jr/i)).toBeInTheDocument()
    expect(api.getVacante).toHaveBeenCalledWith('backend-jr')
    expect(within(screen.getByRole('list', { name: /criterios/i })).getAllByRole('listitem')[0]).toHaveTextContent('50 %')
  })

  it('si la vacante no existe usa los pesos genéricos', async () => {
    vi.mocked(api.getVacante).mockRejectedValue(new api.ApiError(404, 'x'))
    setup('/como-evaluamos?vacante=nada')
    await vi.waitFor(() => expect(api.getVacante).toHaveBeenCalled())
    expect(within(screen.getByRole('list', { name: /criterios/i })).getAllByRole('listitem')[0]).toHaveTextContent('45 %')
  })

  it('explica que la IA solo sugiere, que decide una persona y qué datos se ocultan', () => {
    setup()
    expect(screen.getByText(/la ia solo extrae información y sugiere/i)).toBeInTheDocument()
    expect(screen.getByText(/una persona decide/i)).toBeInTheDocument()
    expect(screen.getByText(/nombre, género, edad y origen se ocultan/i)).toBeInTheDocument()
  })

  it('lista los derechos de la Ley 1581 y el correo de contacto', () => {
    setup()
    const derechos = screen.getByRole('list', { name: /tus derechos/i })
    for (const d of [/conocer/i, /actualizar/i, /rectificar/i, /revocar/i, /revisión humana/i]) {
      expect(within(derechos).getByText(d)).toBeInTheDocument()
    }
    expect(screen.getByRole('link', { name: /privacidad@nexodigital\.example/ })).toHaveAttribute('href', 'mailto:privacidad@nexodigital.example')
  })
})

describe('Privacidad', () => {
  it('enlaza a la página Cómo evaluamos', () => {
    render(<MemoryRouter><Privacidad /></MemoryRouter>)
    expect(screen.getByRole('link', { name: /cómo evaluamos/i })).toHaveAttribute('href', '/como-evaluamos')
  })
})
