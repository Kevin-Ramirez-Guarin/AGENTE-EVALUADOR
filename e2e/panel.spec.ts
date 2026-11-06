import { expect, test, type Page } from '@playwright/test'

const PDF = Buffer.from('%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF')

async function postularYAbrirDetalle(page: Page, nombre: string) {
  await page.goto('/aplicar/backend-jr')
  await page.getByLabel('Nombre completo').fill(nombre)
  await page.getByLabel('Correo electrónico').fill('e2e@example.com')
  await page.getByLabel(/hoja de vida/i).setInputFiles({ name: 'hv.pdf', mimeType: 'application/pdf', buffer: PDF })
  await page.getByRole('checkbox', { name: /autorizo/i }).check()
  await page.getByRole('button', { name: /enviar/i }).click()
  await expect(page.getByRole('status')).toContainText('Recibimos tu postulación')

  await page.getByRole('link', { name: 'Panel' }).click()
  await expect(page.getByText('Demo sin autenticación')).toBeVisible()
  const fila = page.getByRole('row', { name: new RegExp(nombre) })
  await expect(fila).toContainText('pendiente_revision')
  await fila.getByRole('link', { name: nombre }).click()
  await expect(page.getByRole('heading', { name: nombre })).toBeVisible()
}

test('el candidato aplica y el reclutador ve el ranking, el detalle y decide ENTREVISTA', async ({ page }) => {
  const nombre = `Candidata E2E ${Date.now()}`
  await postularYAbrirDetalle(page, nombre)

  await expect(page.getByText(/puntaje total/i)).toBeVisible()
  await expect(page.getByText('Resultado simulado, no proviene del agente real.')).toBeVisible()
  await expect(page.getByText('La IA recomienda; la decisión es tuya.')).toBeVisible()

  const mensajes: string[] = []
  page.on('dialog', (d) => {
    mensajes.push(d.message())
    void d.accept()
  })
  await page.getByLabel('Nombre del reclutador').fill('Reclutadora E2E')
  await page.getByLabel('Veredicto').selectOption('ENTREVISTA')
  await page.getByLabel(/motivo/i).fill('Decisión de la prueba e2e') // necesario si el falso no sugiere ENTREVISTA
  await page.getByRole('button', { name: /registrar decisión/i }).click()

  await expect(page.getByRole('status')).toContainText('decidida')
  await expect(page.getByLabel('Veredicto')).toBeDisabled()
  expect(mensajes).toHaveLength(1)
  expect(mensajes[0]).toContain('Se enviará un correo al candidato')
})

test('con un veredicto distinto del sugerido y sin motivo no se envía y se muestra el error', async ({ page }) => {
  const nombre = `Candidato Sin Motivo ${Date.now()}`
  await postularYAbrirDetalle(page, nombre)

  let dialogos = 0
  page.on('dialog', (d) => {
    dialogos++
    void d.dismiss()
  })
  const sugerido = (await page.getByText(/la ia sugiere:/i).textContent()) ?? ''
  await page.getByLabel('Nombre del reclutador').fill('Reclutadora E2E')
  await page.getByLabel('Veredicto').selectOption(sugerido.includes('NO_CONTINUA') ? 'ENTREVISTA' : 'NO_CONTINUA')
  await page.getByRole('button', { name: /registrar decisión/i }).click()

  await expect(page.getByRole('alert')).toContainText(/motivo/i)
  await expect(page.getByLabel('Veredicto')).toBeEnabled()
  expect(dialogos).toBe(0)
})
