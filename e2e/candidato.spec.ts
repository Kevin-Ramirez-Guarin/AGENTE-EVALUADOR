import { expect, test } from '@playwright/test'
import { PDF } from './helpers'


test('el candidato se postula y ve el mensaje de éxito sin puntaje', async ({ page }) => {
  await page.goto('/vacantes')
  await expect(page.getByRole('heading', { name: /backend jr/i })).toBeVisible()
  await page.getByRole('link', { name: /aplicar a .*backend jr/i }).click()

  await page.getByLabel('Nombre completo').fill('Ana Pérez')
  await page.getByLabel('Correo electrónico').fill('ana@example.com')
  await page.getByLabel(/hoja de vida/i).setInputFiles({ name: 'hv.pdf', mimeType: 'application/pdf', buffer: PDF })
  await page.getByRole('checkbox', { name: /autorizo/i }).check()
  await page.getByRole('button', { name: /enviar/i }).click()

  await expect(page.getByRole('status')).toContainText('Recibimos tu postulación')
  await expect(page.getByText(/puntaje|veredicto/i)).toHaveCount(0)
})
