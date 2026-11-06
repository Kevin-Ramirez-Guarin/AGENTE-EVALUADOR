import { expect, type Page } from '@playwright/test'

// PDF mínimo válido generado en la prueba.
export const PDF = Buffer.from('%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF')

export async function aplicar(page: Page, nombre: string) {
  await page.goto('/aplicar/backend-jr')
  await page.getByLabel('Nombre completo').fill(nombre)
  await page.getByLabel('Correo electrónico').fill('e2e@example.com')
  await page.getByLabel(/hoja de vida/i).setInputFiles({ name: 'hv.pdf', mimeType: 'application/pdf', buffer: PDF })
  await page.getByRole('checkbox', { name: /autorizo/i }).check()
  await page.getByRole('button', { name: /enviar/i }).click()
  await expect(page.getByRole('status')).toContainText('Recibimos tu postulación')
}

// Tolera el backend síncrono (ya trae puntaje) y el asíncrono (pasa por "En evaluación"):
// refresca el panel hasta que la fila queda en "Pendiente de revisión", con puntaje.
export async function esperarFilaEvaluada(page: Page, nombre: string) {
  await page.getByRole('link', { name: 'Panel' }).click()
  await expect(page.getByText('Demo sin autenticación')).toBeVisible()
  const fila = page.getByRole('row', { name: new RegExp(nombre) })
  await expect(async () => {
    await page.getByRole('button', { name: 'Actualizar' }).click()
    await expect(fila).toContainText('Pendiente de revisión', { timeout: 1500 })
  }).toPass({ timeout: 60_000 })
  return fila
}

export async function postularYAbrirDetalle(page: Page, nombre: string) {
  await aplicar(page, nombre)
  const fila = await esperarFilaEvaluada(page, nombre)
  await fila.getByRole('link', { name: nombre }).click()
  await expect(page.getByRole('heading', { name: nombre })).toBeVisible()
  await expect(page.getByText(/puntaje total/i)).toBeVisible()
}
