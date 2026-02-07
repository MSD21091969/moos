/**
 * Test UI Fixes: P2-EDIT-001 and P2-CACHE-001
 * 
 * P2-EDIT-001: Session edits should persist to Firestore
 * P2-CACHE-001: New child sessions should appear immediately
 */

import { test, expect, Page } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'
const API_BASE = 'http://localhost:8000'

async function loginAsEnterprise(page: Page) {
  // Set auth in localStorage
  await page.evaluate(() => {
    localStorage.setItem('user_id', 'enterprise@test.com')
    localStorage.setItem('auth_token', 'test-token-for-skip-auth')
  })
  
  await page.goto(BASE_URL)
  await page.waitForLoadState('networkidle')
}

test.describe('P2-EDIT-001: Session Persistence', () => {
  test('Edit session title persists to Firestore', async ({ page }) => {
    await loginAsEnterprise(page)
    
    // 1. Wait for canvas and create a session
    await page.waitForSelector('[data-testid="canvas"]', { timeout: 5000 })
    await page.click('[data-testid="root-node"]')
    await page.click('[data-testid="context-menu-add-session"]')
    
    // 2. Get the new session ID
    const sessionElements = await page.locator('[data-testid*="session-"]').all()
    const lastSession = sessionElements[sessionElements.length - 1]
    const sessionId = await lastSession.getAttribute('data-testid')
    
    console.log(`Created session: ${sessionId}`)
    
    // 3. Edit the title
    const originalTitle = 'Test Edit Session'
    await lastSession.click()
    await page.click('[data-testid="session-edit-btn"]')
    await page.fill('[data-testid="session-title-input"]', originalTitle)
    await page.click('[data-testid="session-save-btn"]')
    
    // 4. Wait a moment for the API call
    await page.waitForTimeout(500)
    
    // 5. Reload the page and verify title persists
    await page.reload()
    await page.waitForSelector('[data-testid="canvas"]', { timeout: 5000 })
    
    const reloadedSession = page.locator(`[data-testid="${sessionId}"]`)
    const persistedTitle = await reloadedSession.getAttribute('data-title')
    
    expect(persistedTitle).toBe(originalTitle)
    console.log('✅ P2-EDIT-001: Title persisted to Firestore')
  })
})

test.describe('P2-CACHE-001: Cache Invalidation', () => {
  test('New child session appears immediately without refresh', async ({ page }) => {
    await loginAsEnterprise(page)
    
    // 1. Wait for canvas and create parent session
    await page.waitForSelector('[data-testid="canvas"]', { timeout: 5000 })
    await page.click('[data-testid="root-node"]')
    await page.click('[data-testid="context-menu-add-session"]')
    
    // 2. Get parent session
    const sessionElements = await page.locator('[data-testid*="session-"]').all()
    const parentSession = sessionElements[sessionElements.length - 1]
    await parentSession.click()
    
    // 3. Navigate into parent
    await page.dblClick(parentSession)
    await page.waitForSelector('[data-testid="canvas"]', { timeout: 5000 })
    
    // 4. Get current session count
    const initialChildren = await page.locator('[data-testid*="session-"]').all()
    const initialCount = initialChildren.length
    
    // 5. Create child session
    await page.click('[data-testid="breadcrumb-add"]')
    await page.click('[data-testid="context-menu-add-session"]')
    
    // 6. Verify new child appears immediately (without manual refresh)
    await page.waitForTimeout(200) // Brief wait for DOM update
    const updatedChildren = await page.locator('[data-testid*="session-"]').all()
    const updatedCount = updatedChildren.length
    
    expect(updatedCount).toBe(initialCount + 1)
    console.log('✅ P2-CACHE-001: New child appeared immediately without refresh')
  })
})

test.describe('Phase 2 Stability', () => {
  test('Backend integration working', async ({ page }) => {
    await loginAsEnterprise(page)
    
    // Verify backend responds
    const health = await page.evaluate(async () => {
      const resp = await fetch('http://localhost:8000/health')
      return resp.json()
    })
    
    expect(health.status).toBe('healthy')
    console.log('✅ Backend integration verified')
  })
})
