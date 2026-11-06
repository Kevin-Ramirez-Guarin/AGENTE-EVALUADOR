import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from '../api'
import { Detalle } from './Detalle'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  getEvaluacion: vi.fn(),
  decidir: vi.fn(),
  reintentarEvaluacion: vi.fn(),
}))

const criterio = (c: api.NombreCriterio, puntaje: number): api.CriterioDetalle => ({
  criterio: c,
  puntaje,
  peso: 0.45,
  cumplidos: [`cumple-${c}`],
  faltantes: [`falta-${c}`],
  evidencias: [`evid-${c}`],
  nota: `nota-${c}`,
})

const base: api.EvaluacionDetalle & { perfil: api.Perfil; resultado: api.Resultado } = {
  id: 12,
  vacante_id: 'backend-jr',
  candidato: 'Ana Pérez',
  perfil: {
    habilidades_tecnicas: [{ nombre: 'Python', nivel: 'avanzado', evidencia: '2 años desarrollando APIs en Python' }],
    habilidades_blandas: [{ nombre: 'Trabajo en equipo', nivel: 'intermedio', evidencia: 'Lideró dailies' }],
    anios_experiencia: 2,
    nivel_educativo: 'tecnologo',
    idiomas: [],
    fortalezas: ['Dominio de Python'],
    debilidades: ['Poca experiencia con Docker'],
    resumen: 'Desarrolladora backend con 2 años de experiencia.',
  },
  resultado: {
    puntaje_total: 82.5,
    puntajes_por_criterio: { tecnico: 88, experiencia: 80, blandas: 70, educacion: 100, idiomas: 100 },
    criterios: [criterio('tecnico', 88), criterio('experiencia', 80)],
    veredicto_sugerido: 'ENTREVISTA',
    cumple_obligatorios: true,
    explicacion: 'Cumple los 3 requisitos obligatorios con evidencia en la HV.',
    mejor_vacante_alternativa: 'frontend-jr',
  },
  veredicto_final: null,
  estado: 'pendiente_revision',
  error: null,
}

const renderAt = (id: number) =>
  render(
    <MemoryRouter initialEntries={[`/panel/${id}`]}>
      <Routes>
        <Route path="/panel/:id" element={<Detalle />} />
      </Routes>
    </MemoryRouter>,
  )

const setup = async (ev: api.EvaluacionDetalle = base) => {
  vi.mocked(api.getEvaluacion).mockResolvedValue(ev)
  renderAt(12)
  await screen.findByRole('heading', { name: /ana pérez/i })
  return userEvent.setup()
}

const registrar = async (user: ReturnType<typeof userEvent.setup>) => {
  await user.type(screen.getByLabelText(/reclutador/i), 'jvarz12')
  await user.click(screen.getByRole('button', { name: /registrar decisión/i }))
}

describe('Detalle', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    localStorage.clear()
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('explica la decisión: perfil, habilidades con evidencia, puntaje, obligatorios y sugerencia', async () => {
    await setup()
    expect(screen.getByText(base.perfil.resumen)).toBeInTheDocument()
    expect(screen.getByText('Dominio de Python')).toBeInTheDocument()
    expect(screen.getByText('Poca experiencia con Docker')).toBeInTheDocument()
    expect(screen.getByText(/2 años desarrollando APIs/)).toBeInTheDocument()
    expect(screen.getByText(/lideró dailies/i)).toBeInTheDocument()
    expect(screen.getByText(/puntaje total: 82.5/i)).toBeInTheDocument()
    expect(screen.getByText(/cumple los obligatorios: sí/i)).toBeInTheDocument()
    expect(screen.getByText(/la ia sugiere: ENTREVISTA/i)).toBeInTheDocument()
    expect(screen.getByText(base.resultado.explicacion)).toBeInTheDocument()
    expect(screen.getByText(/frontend-jr/)).toBeInTheDocument()
    expect(screen.getByText(/la ia recomienda; la decisión es tuya/i)).toBeInTheDocument()
  })

  it('por criterio muestra barra con texto, peso, cumplido, faltante, evidencia y nota', async () => {
    await setup()
    const barra = screen.getByRole('meter', { name: /técnico/i })
    expect(barra).toHaveAttribute('aria-valuenow', '88')
    expect(barra).toHaveAttribute('aria-valuetext', '88 de 100')
    for (const t of ['cumple-tecnico', 'falta-tecnico', 'evid-tecnico', 'nota-tecnico', 'cumple-experiencia']) {
      expect(screen.getByText(t)).toBeInTheDocument()
    }
    expect(screen.getAllByText(/peso 45 %/i).length).toBeGreaterThan(0)
  })

  it('si criterios viene vacío o falta, cae a puntajes_por_criterio', async () => {
    await setup({ ...base, resultado: { ...base.resultado, criterios: [] } })
    expect(screen.getByRole('meter', { name: /blandas/i })).toHaveAttribute('aria-valuenow', '70')
    expect(screen.getByRole('meter', { name: /idiomas/i })).toHaveAttribute('aria-valuenow', '100')
    expect(screen.queryByText('cumple-tecnico')).not.toBeInTheDocument()
  })

  it('pide motivo cuando el veredicto difiere del sugerido y no envía', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText(/veredicto/i), 'NO_CONTINUA')
    await registrar(user)
    expect(await screen.findByRole('alert')).toHaveTextContent(/motivo/i)
    expect(api.decidir).not.toHaveBeenCalled()
  })

  it('decide con éxito tras confirmar, recuerda el nombre y muestra fecha y Meet', async () => {
    const confirmar = vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.decidir).mockResolvedValue({
      id: 12,
      veredicto_final: 'ENTREVISTA',
      estado: 'decidida',
      entrevista: { inicio: '2026-11-09T10:00:00-05:00', meet_link: 'https://meet.google.com/xxx-xxxx-xxx' },
    })
    const user = await setup()
    await registrar(user)

    expect(confirmar).toHaveBeenCalledWith(expect.stringMatching(/se enviará un correo al candidato/i))
    expect(api.decidir).toHaveBeenCalledWith(12, { veredicto: 'ENTREVISTA', motivo: undefined, reclutador: 'jvarz12' })
    expect(await screen.findByText(/decidida/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /meet/i })).toHaveAttribute('href', 'https://meet.google.com/xxx-xxxx-xxx')
    expect(localStorage.getItem('reclutador')).toBe('jvarz12')
    expect(screen.getByLabelText(/veredicto/i)).toBeDisabled()
  })

  it('no envía si el reclutador cancela la confirmación', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    const user = await setup()
    await registrar(user)
    expect(api.decidir).not.toHaveBeenCalled()
  })

  it('precarga el nombre guardado en localStorage', async () => {
    localStorage.setItem('reclutador', 'guardado')
    await setup()
    expect(screen.getByLabelText(/reclutador/i)).toHaveValue('guardado')
  })

  it.each([
    [409, /ya fue decidida/i],
    [422, /motivo/i],
    [404, /no existe/i],
  ])('muestra un mensaje claro para el error %i', async (status, msg) => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.decidir).mockRejectedValue(new api.ApiError(status, 'x'))
    const user = await setup()
    await registrar(user)
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(msg))
  })

  it('si ya está decidida no muestra el formulario y sí el veredicto final', async () => {
    await setup({ ...base, estado: 'decidida', veredicto_final: 'REVISION_HUMANA' })
    expect(screen.queryByRole('button', { name: /registrar decisión/i })).not.toBeInTheDocument()
    expect(screen.getByText(/veredicto final: REVISION_HUMANA/i)).toBeInTheDocument()
  })

  it('rotula la nota por criterio como texto para la persona candidata', async () => {
    await setup()
    expect(screen.getAllByText(/nota para la persona candidata \(se usa en el correo\)/i)).toHaveLength(2)
  })

  describe('estados asíncronos', () => {
    const enCurso: api.EvaluacionDetalle = { ...base, perfil: null, resultado: null, estado: 'en_evaluacion' }
    const conError: api.EvaluacionDetalle = { ...enCurso, estado: 'error_evaluacion', error: 'El servicio de IA no respondió.' }

    it('en_evaluacion avisa que la IA analiza la HV y no muestra el formulario', async () => {
      await setup(enCurso)
      expect(screen.getByText(/la ia está analizando esta hoja de vida/i)).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /registrar decisión/i })).not.toBeInTheDocument()
      expect(screen.queryByText(/puntaje total/i)).not.toBeInTheDocument()
    })

    it('en_evaluacion se refresca cada 5 s hasta que llega el resultado y limpia el intervalo', async () => {
      vi.useFakeTimers()
      vi.mocked(api.getEvaluacion).mockResolvedValue(enCurso)
      const { unmount } = render(<MemoryRouter initialEntries={['/panel/12']}><Routes><Route path="/panel/:id" element={<Detalle />} /></Routes></MemoryRouter>)
      await act(() => vi.advanceTimersByTimeAsync(0))
      expect(api.getEvaluacion).toHaveBeenCalledTimes(1)
      vi.mocked(api.getEvaluacion).mockResolvedValue(base)
      await act(() => vi.advanceTimersByTimeAsync(5000))
      expect(api.getEvaluacion).toHaveBeenCalledTimes(2)
      expect(screen.getByText(/puntaje total: 82.5/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /registrar decisión/i })).toBeInTheDocument()
      await act(() => vi.advanceTimersByTimeAsync(15000))
      expect(api.getEvaluacion).toHaveBeenCalledTimes(2)
      unmount()
    })

    it('error_evaluacion muestra el mensaje de error y el botón Reintentar, sin formulario', async () => {
      await setup(conError)
      expect(screen.getByRole('alert')).toHaveTextContent('El servicio de IA no respondió.')
      expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /registrar decisión/i })).not.toBeInTheDocument()
    })

    it('Reintentar llama a la API y recarga la evaluación', async () => {
      vi.mocked(api.reintentarEvaluacion).mockResolvedValue(undefined)
      const user = await setup(conError)
      vi.mocked(api.getEvaluacion).mockResolvedValue(enCurso)
      await user.click(screen.getByRole('button', { name: /reintentar/i }))
      expect(api.reintentarEvaluacion).toHaveBeenCalledWith(12)
      expect(await screen.findByText(/la ia está analizando/i)).toBeInTheDocument()
    })

    it('si Reintentar responde 409 recarga el estado actual', async () => {
      vi.mocked(api.reintentarEvaluacion).mockRejectedValue(new api.ApiError(409, 'x'))
      const user = await setup(conError)
      vi.mocked(api.getEvaluacion).mockResolvedValue(base)
      await user.click(screen.getByRole('button', { name: /reintentar/i }))
      expect(await screen.findByText(/puntaje total/i)).toBeInTheDocument()
    })
  })

  it('avisa si la evaluación no existe', async () => {
    vi.mocked(api.getEvaluacion).mockRejectedValue(new api.ApiError(404, 'x'))
    renderAt(99)
    expect(await screen.findByRole('alert')).toHaveTextContent(/no existe/i)
  })

  it('el respaldo sin criterios no muestra un peso falso', async () => {
    await setup({ ...base, resultado: { ...base.resultado, criterios: [] } })
    expect(screen.queryByText(/peso/i)).not.toBeInTheDocument()
  })

  it('el texto del puntaje de la barra está oculto a lectores de pantalla', async () => {
    await setup()
    expect(screen.getByText('88 / 100')).toHaveAttribute('aria-hidden', 'true')
  })

  it('el enlace de Meet https abre en pestaña nueva con rel seguro', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.decidir).mockResolvedValue({ id: 12, veredicto_final: 'ENTREVISTA', estado: 'decidida', entrevista: { inicio: '2026-11-09T10:00:00-05:00', meet_link: 'https://meet.google.com/a' } })
    const user = await setup()
    await registrar(user)
    const enlace = await screen.findByRole('link', { name: /meet/i })
    expect(enlace).toHaveAttribute('target', '_blank')
    expect(enlace).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('un meet_link que no es https no se muestra como enlace', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(api.decidir).mockResolvedValue({ id: 12, veredicto_final: 'ENTREVISTA', estado: 'decidida', entrevista: { inicio: '2026-11-09T10:00:00-05:00', meet_link: 'javascript:alert(1)' } })
    const user = await setup()
    await registrar(user)
    await screen.findByText(/estado: decidida/i)
    expect(screen.queryByRole('link', { name: /meet/i })).not.toBeInTheDocument()
  })

  it('al navegar a otra evaluación ignora la respuesta tardía de la anterior', async () => {
    let resolver12: (e: api.EvaluacionDetalle) => void = () => {}
    vi.mocked(api.getEvaluacion).mockImplementation((id) =>
      id === 12 ? new Promise((r) => (resolver12 = r)) : Promise.resolve({ ...base, id: 13, candidato: 'Luis Gómez' }),
    )
    render(
      <MemoryRouter initialEntries={['/panel/12']}>
        <Link to="/panel/13">ir</Link>
        <Routes>
          <Route path="/panel/:id" element={<Detalle />} />
        </Routes>
      </MemoryRouter>,
    )
    await userEvent.setup().click(screen.getByRole('link', { name: 'ir' }))
    await screen.findByRole('heading', { name: /luis gómez/i })
    resolver12(base)
    await new Promise((r) => setTimeout(r, 20))
    expect(screen.getByRole('heading', { name: /luis gómez/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /ana pérez/i })).not.toBeInTheDocument()
  })
})
