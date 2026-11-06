import { expect, test } from '@playwright/test'

const PDF = Buffer.from('%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF')

test('el candidato aplica y el reclutador ve el ranking, el detalle y decide ENTREVISTA', async ({ page }) => {
  const nombre = `Candidata E2E ${Date.now()}`

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
  await expect(page.getByText(/puntaje total/i)).toBeVisible()
  await expect(page.getByText('Resultado simulado, no proviene del agente real.')).toBeVisible()
  await expect(page.getByText('La IA recomienda; la decisión es tuya.')).toBeVisible()

  await page.getByLabel('Nombre del reclutador').fill('Reclutadora E2E')
  await page.getByLabel('Veredicto').selectOption('ENTREVISTA')
  await page.getByLabel(/motivo/i).fill('Decisión de la prueba e2e') // necesario si el falso no sugiere ENTREVISTA
  page.once('dialog', (d) => {
    expect(d.message()).toContain('Se enviará un correo al candidato')
    return d.accept()
  })
  await page.getByRole('button', { name: /registrar decisión/i }).click()

  await expect(page.getByRole('status')).toContainText('decidida')
  await expect(page.getByLabel('Veredicto')).toBeDisabled()
})
