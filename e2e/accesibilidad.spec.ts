import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { postularYAbrirDetalle } from './helpers'

// 0 violaciones serias o críticas (WCAG 2.x A/AA).
async function sinViolacionesGraves(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
  const graves = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
  expect(graves.map((v) => `${v.id}: ${v.nodes.map((n) => n.target).join(' | ')}`)).toEqual([])
}

const RUTAS: [string, string, RegExp][] = [
  ['/vacantes', 'vacantes', /vacantes abiertas/i],
  ['/aplicar/backend-jr', 'aplicar', /backend jr/i],
  ['/privacidad', 'privacidad', /política de privacidad/i],
  ['/como-evaluamos?vacante=backend-jr', 'cómo evaluamos', /cómo evaluamos/i],
]

for (const [ruta, nombre, titulo] of RUTAS) {
  test(`accesibilidad: ${nombre} no tiene violaciones serias ni críticas`, async ({ page }) => {
    await page.goto(ruta)
    await expect(page.getByRole('heading', { level: 1, name: titulo })).toBeVisible()
    await sinViolacionesGraves(page)
  })
}

test('accesibilidad: /panel y /panel/:id con datos no tienen violaciones serias ni críticas', async ({ page }) => {
  await postularYAbrirDetalle(page, `Candidata Axe ${Date.now()}`)
  await sinViolacionesGraves(page) // detalle
  await page.getByRole('link', { name: /volver al panel/i }).click()
  await expect(page.getByRole('table')).toBeVisible()
  await sinViolacionesGraves(page) // panel
})
