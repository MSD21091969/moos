import { chromium } from 'playwright';

async function connectToEdge() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const contexts = browser.contexts();
  
  console.log(`Connected to Edge. Found ${contexts.length} context(s)`);
  
  for (const context of contexts) {
    const pages = context.pages();
    console.log(`Context has ${pages.length} page(s)`);
    
    for (const page of pages) {
      console.log(`- ${page.url()}`);
    }
  }
  
  // Find workspace page
  const workspacePage = contexts
    .flatMap(ctx => ctx.pages())
    .find(p => p.url().includes('localhost:5173/workspace'));
  
  if (workspacePage) {
    console.log('\n✅ Found workspace page');
    
    // Get localStorage
    const storage = await workspacePage.evaluate(() => {
      const data = localStorage.getItem('workspace-storage');
      return data ? JSON.parse(data) : null;
    });
    
    console.log('\n📦 localStorage state:');
    console.log(JSON.stringify(storage?.state, null, 2));
  } else {
    console.log('\n❌ Workspace page not found');
  }
  
  await browser.close();
}

connectToEdge().catch(console.error);
