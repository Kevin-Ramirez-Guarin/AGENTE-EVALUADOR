import { expect, test } from '@playwright/test'
import { postularYAbrirDetalle } from './helpers'

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

  await expect(page.getByRole('status')).toContainText(/decidida/i)
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
  await page.getByLabel('Veredicto').selectOption(/no continúa/i.test(sugerido) ? 'ENTREVISTA' : 'NO_CONTINUA')
  await page.getByRole('button', { name: /registrar decisión/i }).click()

  await expect(page.getByRole('alert')).toContainText(/motivo/i)
  await expect(page.getByLabel('Veredicto')).toBeEnabled()
  expect(dialogos).toBe(0)
})
