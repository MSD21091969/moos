import { chromium } from 'playwright';

async function tailConsole() {
  console.log('🔌 Connecting to browser to tail logs...');
  try {
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const context = browser.contexts()[0];
    if (!context) {
        console.log('❌ No context found');
        process.exit(1);
    }
    const page = context.pages().find(p => p.url().includes('localhost:5173')) || context.pages()[0];
    if (!page) {
        console.log('❌ No page found');
        process.exit(1);
    }

    console.log(`📺 Tailing console for: ${page.url()}`);

    page.on('console', msg => {
      const text = msg.text();
      // Filter for our observer tags or errors
      if (text.startsWith('[CLICK]') || 
          text.startsWith('[NAV]') || 
          text.startsWith('[STATE]') || 
          text.startsWith('[ERROR]') ||
          text.startsWith('[CONTEXT]') ||
          text.startsWith('[MODAL]')) {
        console.log(text);
      }
    });

    // Keep alive forever
    await new Promise(() => {}); 
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

tailConsole();