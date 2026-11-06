import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
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

  it('muestra el error del servidor y permite reintentar', async () => {
    vi.mocked(api.enviarPostulacion).mockRejectedValue(new api.ApiError(415, 'no es PDF'))
    const user = setup()
    await fill(user)
    await submit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent(/no pudimos enviar/i)
    expect(screen.getByRole('button', { name: /enviar/i })).toBeEnabled()
  })
})
