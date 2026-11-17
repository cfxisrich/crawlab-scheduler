import { expect, test } from '@playwright/test'

test('unauthenticated navigation shows login without a false session-expired error', async ({ page }) => {
  await page.goto('/#runs')
  await expect(page.getByRole('heading', { name: '登录工作台' })).toBeVisible()
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.getByRole('navigation')).toHaveCount(0)
  await page.screenshot({ path: '../docs/screenshots/login.png', fullPage: true })
})

test('unavailable engine is shown as an actionable login error', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('用户名').fill('browser-test')
  await page.getByLabel('密码', { exact: true }).fill('not-a-real-account')
  await page.getByRole('button', { name: '进入工作台' }).click()
  await expect(page.getByRole('alert')).toContainText('Crawlab')
  await expect(page.getByRole('heading', { name: '登录工作台' })).toBeVisible()
  await expect(page.getByRole('button', { name: '进入工作台' })).toBeEnabled()
})

test('login is usable on a narrow viewport with no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '登录工作台' })).toBeVisible()
  await expect(page.getByLabel('用户名')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: '../docs/screenshots/login-mobile.png', fullPage: true })
})
