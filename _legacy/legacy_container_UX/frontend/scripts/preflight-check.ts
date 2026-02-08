/**
 * Pre-flight Check Script
 * 
 * Validates that the development environment is correctly configured
 * before running tests or starting development.
 * 
 * Usage: npx tsx scripts/preflight-check.ts
 */

import fs from 'fs';
import path from 'path';

interface CheckResult {
  name: string;
  passed: boolean;
  message: string;
}

const results: CheckResult[] = [];

function check(name: string, condition: boolean, passMsg: string, failMsg: string) {
  results.push({
    name,
    passed: condition,
    message: condition ? passMsg : failMsg
  });
}

async function runChecks() {
  console.log('🔍 Running Pre-flight Checks...\n');
  
  const frontendDir = process.cwd();
  const rootDir = path.dirname(frontendDir);
  
  // 1. Check .env.development exists
  const envPath = path.join(frontendDir, '.env.development');
  const envExists = fs.existsSync(envPath);
  check(
    'Environment File',
    envExists,
    '.env.development exists',
    '.env.development NOT FOUND - create it from .env.example'
  );
  
  // 2. Check VITE_MODE
  if (envExists) {
    const envContent = fs.readFileSync(envPath, 'utf-8');
    const modeMatch = envContent.match(/VITE_MODE=(\w+)/);
    const mode = modeMatch?.[1];
    
    // Check if we are in Phase 2 (backend running) or Phase 1 (demo)
    // For now, we just warn if it's not demo, but don't fail if it's development (Phase 2)
    const isPhase2 = mode === 'development';
    const isPhase1 = mode === 'demo';
    
    check(
      'VITE_MODE',
      isPhase1 || isPhase2,
      `VITE_MODE=${mode} (valid for ${isPhase1 ? 'Phase 1' : 'Phase 2'})`,
      `VITE_MODE=${mode || 'not set'} - should be 'demo' (Phase 1) or 'development' (Phase 2)`
    );
  }
  
  // 3. Check package.json exists
  const pkgPath = path.join(frontendDir, 'package.json');
  const pkgExists = fs.existsSync(pkgPath);
  check(
    'Package.json',
    pkgExists,
    'package.json found',
    'package.json NOT FOUND - are you in the frontend directory?'
  );
  
  // 4. Check node_modules exists
  const nmPath = path.join(frontendDir, 'node_modules');
  const nmExists = fs.existsSync(nmPath);
  check(
    'Dependencies',
    nmExists,
    'node_modules exists',
    'node_modules NOT FOUND - run npm install'
  );
  
  // 5. Check Playwright is installed
  const pwPath = path.join(frontendDir, 'node_modules', '@playwright', 'test');
  const pwExists = fs.existsSync(pwPath);
  check(
    'Playwright',
    pwExists,
    'Playwright installed',
    'Playwright NOT FOUND - run npm install'
  );
  
  // 6. Check demo-data.ts exists
  const demoDataPath = path.join(frontendDir, 'src', 'lib', 'demo-data.ts');
  const demoDataExists = fs.existsSync(demoDataPath);
  check(
    'Demo Data',
    demoDataExists,
    'demo-data.ts exists',
    'demo-data.ts NOT FOUND - demo mode won\'t work'
  );
  
  // 7. Check smoke test exists (Phase 1)
  // In Phase 2, we might have renamed it or moved on, so this is optional if in Phase 2
  const smokeTestPath = path.join(frontendDir, 'tests', 'e2e', 'demo-smoke.spec.ts');
  const phase1TestPath = path.join(frontendDir, 'tests', 'e2e', 'phase1-ux-guardrails.spec.ts');
  const smokeTestExists = fs.existsSync(smokeTestPath) || fs.existsSync(phase1TestPath);
  
  // Only enforce smoke test in Phase 1
  const envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf-8') : '';
  const modeMatch = envContent.match(/VITE_MODE=(\w+)/);
  const mode = modeMatch?.[1];
  const isPhase2 = mode === 'development';

  if (!isPhase2) {
    check(
      'Smoke Tests',
      smokeTestExists,
      'Smoke tests found',
      'demo-smoke.spec.ts or phase1-ux-guardrails.spec.ts NOT FOUND - create it for UX validation'
    );
  }
  
  // 8. Check container-slice.ts has demo mode handling
  const storePath = path.join(frontendDir, 'src', 'lib', 'store', 'container-slice.ts');
  if (fs.existsSync(storePath)) {
    const storeContent = fs.readFileSync(storePath, 'utf-8');
    const hasDemoMode = storeContent.includes("mode === 'demo'");
    check(
      'Store Demo Mode',
      hasDemoMode,
      'container-slice.ts handles demo mode',
      'container-slice.ts may not handle demo mode correctly'
    );
  }
  
  // Print results
  console.log('═══════════════════════════════════════════════════════════');
  console.log('  Pre-flight Check Results');
  console.log('═══════════════════════════════════════════════════════════\n');
  
  let allPassed = true;
  for (const r of results) {
    const icon = r.passed ? '✅' : '❌';
    console.log(`${icon} ${r.name}: ${r.message}`);
    if (!r.passed) allPassed = false;
  }
  
  console.log('\n═══════════════════════════════════════════════════════════');
  
  if (allPassed) {
    console.log('  ✅ All checks passed! Ready to test.');
    console.log('═══════════════════════════════════════════════════════════\n');
    console.log('  Quick commands:');
    console.log('    npm run dev                    # Start dev server');
    console.log('    npx playwright test demo-smoke # Run smoke tests');
    console.log('');
    process.exit(0);
  } else {
    console.log('  ❌ Some checks failed. Fix issues above before testing.');
    console.log('═══════════════════════════════════════════════════════════\n');
    process.exit(1);
  }
}

runChecks().catch(console.error);
