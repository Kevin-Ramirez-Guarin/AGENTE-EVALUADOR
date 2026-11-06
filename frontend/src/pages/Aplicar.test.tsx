import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as api from '../api'
import { Aplicar } from './Aplicar'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api')>()),
  getVacante: vi.fn(),
  enviarPostulacion: vi.fn(),
}))

const vacante = { id: 'backend-jr', titulo: 'Desarrollador/a Backend Jr (Python)' } as api.Vacante
const MB = 1024 * 1024
const pdf = (bytes = 10, name = 'hv.pdf', type = 'application/pdf') =>
  new File([new Uint8Array(bytes)], name, { type })

type User = ReturnType<typeof userEvent.setup>

const setup = (): User => {
  render(
    <MemoryRouter initialEntries={['/aplicar/backend-jr']}>
      <Routes>
        <Route path="/aplicar/:id" element={<Aplicar />} />
      </Routes>
    </MemoryRouter>,
  )
  return userEvent.setup({ applyAccept: false })
}

const fill = async (user: User, file = pdf(), consent = true) => {
  await screen.findByRole('heading', { name: /backend jr/i })
  await user.type(screen.getByLabelText(/nombre/i), 'Ana Pérez')
  await user.type(screen.getByLabelText(/correo/i), 'ana@example.com')
  await user.upload(screen.getByLabelText(/hoja de vida/i), file)
  if (consent) await user.click(screen.getByRole('checkbox', { name: /autorizo/i }))
}
const submit = (user: User) => user.click(screen.getByRole('button', { name: /enviar/i }))

describe('Aplicar', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(api.getVacante).mockResolvedValue(vacante)
  })

  it('la casilla de autorización arranca sin marcar y explica IA, decisión humana y política', async () => {
    setup()
    const box = await screen.findByRole('checkbox', { name: /autorizo/i })
    expect(box).not.toBeChecked()
    expect(box).toBeRequired()
    expect(screen.getByText(/inteligencia artificial/i)).toBeInTheDocument()
    expect(screen.getByText(/persona/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /pol[ií]tica/i })).toHaveAttribute('href', '/privacidad')
  })

  it('no envía sin autorización y asocia el error al campo', async () => {
    const user = setup()
    await fill(user, pdf(), false)
    await submit(user)

    expect(api.enviarPostulacion).not.toHaveBeenCalled()
    const box = screen.getByRole('checkbox', { name: /autorizo/i })
    expect(box).toBeInvalid()
    expect(box).toHaveAccessibleDescription(/autorizaci[oó]n/i)
  })

  it('rechaza archivos que no son PDF', async () => {
    const user = setup()
    await fill(user, pdf(10, 'hv.docx', 'application/vnd.openxmlformats'))
    await submit(user)

    expect(api.enviarPostulacion).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/hoja de vida/i)).toHaveAccessibleDescription(/pdf/i)
  })

  it('rechaza PDF de más de 5 MB', async () => {
    const user = setup()
    await fill(user, pdf(5 * MB + 1))
    await submit(user)

    expect(api.enviarPostulacion).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/hoja de vida/i)).toHaveAccessibleDescription(/5 ?MB/i)
  })

  it('exige nombre y correo', async () => {
    const user = setup()
    await screen.findByRole('heading', { name: /backend jr/i })
    await submit(user)

    expect(api.enviarPostulacion).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/nombre/i)).toBeInvalid()
    expect(screen.getByLabelText(/correo/i)).toBeInvalid()
  })

  it('envía con éxito y no muestra puntaje ni veredicto', async () => {
    vi.mocked(api.enviarPostulacion).mockResolvedValue({ evaluacion_id: 12, estado: 'pendiente_revision' })
    const user = setup()
    const file = pdf()
    await fill(user, file)
    await submit(user)

    expect(await screen.findByRole('status')).toHaveTextContent(/recibimos tu postulaci[oó]n/i)
    expect(api.enviarPostulacion).toHaveBeenCalledWith({
      vacante_id: 'backend-jr',
      nombre: 'Ana Pérez',
      email: 'ana@example.com',
      pdf: file,
      consentimiento: true,
    })
    expect(screen.queryByText(/puntaje|veredicto|ENTREVISTA|82/i)).not.toBeInTheDocument()
  })

  it('muestra estado de carga mientras envía', async () => {
    let resolver!: (v: api.PostulacionCreada) => void
    vi.mocked(api.enviarPostulacion).mockReturnValue(new Promise((r) => (resolver = r)))
    const user = setup()
    await fill(user)
    await submit(user)

    expect(screen.getByRole('button', { name: /enviando/i })).toBeDisabled()
    resolver({ evaluacion_id: 1, estado: 'pendiente_revision' })
    await waitFor(() => expect(screen.getByRole('status')).toBeInTheDocument())
  })

  it.each([
    [413, /supera los 5 MB/i],
    [415, /no es un PDF/i],
    [422, /autorizaci[oó]n/i],
    [404, /ya no existe/i],
    [500, /no pudimos enviar/i],
  ])('muestra un mensaje específico para el error %i y permite reintentar', async (status, mensaje) => {
    vi.mocked(api.enviarPostulacion).mockRejectedValue(new api.ApiError(status, 'x'))
    const user = setup()
    await fill(user)
    await submit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent(mensaje)
    expect(screen.getByRole('button', { name: /enviar/i })).toBeEnabled()
  })

  it('rechaza un archivo .pdf cuyo tipo MIME no es application/pdf', async () => {
    const user = setup()
    await fill(user, pdf(10, 'hv.pdf', 'text/plain'))
    await submit(user)

    expect(api.enviarPostulacion).not.toHaveBeenCalled()
    expect(screen.getByLabelText(/hoja de vida/i)).toHaveAccessibleDescription(/pdf/i)
  })

  it('mueve el foco al primer campo con error', async () => {
    const user = setup()
    await screen.findByRole('heading', { name: /backend jr/i })
    await submit(user)
    expect(screen.getByLabelText(/nombre/i)).toHaveFocus()

    await user.type(screen.getByLabelText(/nombre/i), 'Ana')
    await user.type(screen.getByLabelText(/correo/i), 'ana@example.com')
    await user.upload(screen.getByLabelText(/hoja de vida/i), pdf())
    await submit(user)
    expect(screen.getByRole('checkbox', { name: /autorizo/i })).toHaveFocus()
  })

  it('ignora la respuesta de una vacante anterior que llega fuera de orden', async () => {
    const resolvers: Record<string, (v: api.Vacante) => void> = {}
    vi.mocked(api.getVacante).mockImplementation((id) => new Promise((r) => (resolvers[id] = r)))
    render(
      <MemoryRouter initialEntries={['/aplicar/a']}>
        <Link to="/aplicar/b">ir a b</Link>
        <Routes>
          <Route path="/aplicar/:id" element={<Aplicar />} />
        </Routes>
      </MemoryRouter>,
    )
    await userEvent.click(screen.getByRole('link', { name: 'ir a b' }))
    await waitFor(() => expect(resolvers.b).toBeDefined())
    resolvers.b({ id: 'b', titulo: 'Vacante B' } as api.Vacante)
    expect(await screen.findByRole('heading', { name: 'Vacante B' })).toBeInTheDocument()
    resolvers.a({ id: 'a', titulo: 'Vacante A' } as api.Vacante)
    await new Promise((r) => setTimeout(r, 20))
    expect(screen.queryByRole('heading', { name: 'Vacante A' })).not.toBeInTheDocument()
  })
})
