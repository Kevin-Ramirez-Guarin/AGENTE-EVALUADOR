import { expect, test } from '@playwright/test'

const PDF = Buffer.from('%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF')

test('sin la autorización marcada el envío no avanza y muestra el error', async ({ page }) => {
  await page.goto('/aplicar/backend-jr')
  await page.getByLabel('Nombre completo').fill('Ana Pérez')
  await page.getByLabel('Correo electrónico').fill('ana@example.com')
  await page.getByLabel(/hoja de vida/i).setInputFiles({ name: 'hv.pdf', mimeType: 'application/pdf', buffer: PDF })
  await page.getByRole('button', { name: /enviar/i }).click()

  await expect(page.getByText(/debes dar tu autorización/i)).toBeVisible()
  await expect(page.getByRole('checkbox', { name: /autorizo/i })).toBeFocused()
  await expect(page.getByRole('status')).toHaveCount(0)
})
