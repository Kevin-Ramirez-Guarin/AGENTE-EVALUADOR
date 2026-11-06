import { expect, test } from '@playwright/test'

test('desde el formulario el candidato llega a Cómo evaluamos con los pesos de la vacante', async ({ page }) => {
  await page.goto('/aplicar/backend-jr')
  // El menú también enlaza a Cómo evaluamos; aquí se usa el enlace del formulario.
  await page.getByRole('main').getByRole('link', { name: /cómo evaluamos/i }).click()

  await expect(page).toHaveURL(/\/como-evaluamos\?vacante=backend-jr/)
  await expect(page.getByRole('heading', { level: 1, name: /cómo evaluamos/i })).toBeVisible()
  await expect(page.getByText(/para la vacante desarrollador\/a backend jr/i)).toBeVisible()
  await expect(page.getByRole('list', { name: /criterios/i }).getByRole('listitem')).toHaveCount(5)
  await expect(page.getByText(/una persona decide/i)).toBeVisible()
  await expect(page.getByRole('link', { name: /privacidad@giveaway\.example/ })).toBeVisible()
})

test('desde la política de privacidad se llega a Cómo evaluamos', async ({ page }) => {
  await page.goto('/privacidad')
  await page.getByRole('main').getByRole('link', { name: /cómo evaluamos/i }).click()
  await expect(page).toHaveURL(/\/como-evaluamos$/)
})
