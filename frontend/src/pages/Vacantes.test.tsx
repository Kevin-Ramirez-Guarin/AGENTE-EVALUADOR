import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from '../api'
import { Vacantes } from './Vacantes'

vi.mock('../api')

const vacante: api.Vacante = {
  id: 'backend-jr',
  titulo: 'Desarrollador/a Backend Jr (Python)',
  requisitos_obligatorios: ['Python', 'SQL', 'Git'],
  deseables: ['FastAPI/Django', 'Docker', 'Testing'],
  blandas: ['Trabajo en equipo'],
  experiencia_min_anios: 1,
  nivel_educativo_min: 'tecnologo',
  idiomas: [{ idioma: 'inglés', nivel: 'A2' }],
  pesos: { tecnico: 0.45, experiencia: 0.25, blandas: 0.15, educacion: 0.1, idiomas: 0.05 },
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <Vacantes />
    </MemoryRouter>,
  )

describe('Vacantes', () => {
  beforeEach(() => vi.resetAllMocks())

  it('muestra título, obligatorios y deseables de cada vacante con enlace para aplicar', async () => {
    vi.mocked(api.getVacantes).mockResolvedValue([vacante])
    renderPage()

    expect(await screen.findByRole('heading', { name: vacante.titulo })).toBeInTheDocument()
    for (const r of [...vacante.requisitos_obligatorios, ...vacante.deseables]) {
      expect(screen.getByText(r)).toBeInTheDocument()
    }
    expect(screen.getByText(/obligatorios/i)).toBeInTheDocument()
    expect(screen.getByText(/deseables/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /aplicar/i })).toHaveAttribute('href', '/aplicar/backend-jr')
  })

  it('muestra equipo, ubicación, modalidad y descripción cuando la API los envía', async () => {
    vi.mocked(api.getVacantes).mockResolvedValue([
      {
        ...vacante,
        equipo: 'Producto y Tecnología',
        ubicacion: 'Medellín, Colombia',
        modalidad: 'Híbrido · Medellín',
        descripcion: 'Construyes el motor de reservas de tours.',
      },
    ])
    renderPage()

    await screen.findByRole('heading', { name: vacante.titulo })
    expect(screen.getByRole('list', { name: /detalles de la vacante/i })).toBeInTheDocument()
    for (const t of ['Producto y Tecnología', 'Medellín, Colombia', 'Híbrido · Medellín', 'Construyes el motor de reservas de tours.']) {
      expect(screen.getByText(t)).toBeInTheDocument()
    }
  })

  it('sin los campos opcionales (o vacíos) no muestra huecos ni etiquetas sueltas', async () => {
    vi.mocked(api.getVacantes).mockResolvedValue([{ ...vacante, equipo: '', descripcion: '' }])
    renderPage()

    await screen.findByRole('heading', { name: vacante.titulo })
    expect(screen.queryByRole('list', { name: /detalles de la vacante/i })).not.toBeInTheDocument()
  })

  it('muestra un mensaje de error si la API falla', async () => {
    vi.mocked(api.getVacantes).mockRejectedValue(new Error('boom'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent(/no pudimos cargar/i)
  })

  it('indica cuando no hay vacantes', async () => {
    vi.mocked(api.getVacantes).mockResolvedValue([])
    renderPage()
    expect(await screen.findByText(/no hay vacantes/i)).toBeInTheDocument()
  })
})
