const puppeteer = require('puppeteer-core');
const http = require('http');

async function getWsUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://172.20.0.2:9223/json/version', (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve(JSON.parse(data).webSocketDebuggerUrl.replace('localhost', '172.20.0.2:9223'));
      });
    }).on('error', reject);
  });
}

(async () => {
  let browser;
  try {
    browser = await puppeteer.connect({ browserWSEndpoint: await getWsUrl(), defaultViewport: null });
    const page = await browser.newPage();
    await page.goto('https://lms.ipexdesenvolvimento.cloud/lms', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 5000));
    
    const layoutInfo = await page.evaluate(() => {
        const app = document.getElementById('app');
        if (!app) return 'No #app found';
        
        // Get immediate children of #app
        const children = Array.from(app.children).map(c => c.className);
        
        // Find the main content area (usually next to sidebar)
        const sidebar = document.querySelector('.bg-surface-menu-bar');
        const mainContent = sidebar ? sidebar.nextElementSibling : null;
        
        return {
            appChildren: children,
            sidebarClasses: sidebar ? sidebar.className : 'None',
            mainContentClasses: mainContent ? mainContent.className : 'None',
            mainContentChildren: mainContent ? Array.from(mainContent.children).map(c => c.className) : []
        };
    });
    console.log(JSON.stringify(layoutInfo, null, 2));
    
    await page.close();
  } catch(e) { console.error(e); }
  finally { if(browser) browser.disconnect(); }
})();
