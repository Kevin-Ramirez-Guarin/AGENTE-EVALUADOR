import { readFileSync } from 'node:fs'
import path from 'node:path'
import { expect, type Page } from '@playwright/test'

// HV sintética real, con texto: el backend extrae el texto al recibir la postulación.
export const PDF = readFileSync(path.resolve(__dirname, '../samples/hv_backend_fuerte_1.pdf'))

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
