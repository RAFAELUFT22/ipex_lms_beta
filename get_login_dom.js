const puppeteer = require('puppeteer-core');
const http = require('http');
const fs = require('fs');

async function getWsUrl() {
  return new Promise((resolve, reject) => {
    http.get('http://172.20.0.2:9223/json/version', (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        const json = JSON.parse(data);
        resolve(json.webSocketDebuggerUrl.replace('localhost', '172.20.0.2:9223'));
      });
    }).on('error', reject);
  });
}

(async () => {
  let browser;
  try {
    const browserWSEndpoint = await getWsUrl();
    browser = await puppeteer.connect({ browserWSEndpoint, defaultViewport: null });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    
    console.log('Navigating to Login page...');
    await page.goto('https://lms.ipexdesenvolvimento.cloud/login', { waitUntil: 'networkidle2' });
    
    const html = await page.content();
    fs.writeFileSync('/root/projeto-tds/login_dom.html', html);
    await page.screenshot({ path: '/root/projeto-tds/debug_login_page.png' });

    console.log('DOM saved to login_dom.html');
    await page.close();
  } catch (e) {
    console.error(e);
  } finally {
    if (browser) await browser.disconnect();
  }
})();
