const puppeteer = require('puppeteer-core');
const http = require('http');

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
    await page.goto('https://lms.ipexdesenvolvimento.cloud/lms', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 3000));
    
    // Dump the innerHTML of the #app element
    const appHtml = await page.evaluate(() => document.getElementById('app').innerHTML);
    const fs = require('fs');
    fs.writeFileSync('/root/projeto-tds/lms_dom.html', appHtml);
    console.log('DOM saved');
    await page.close();
  } catch(e) {
    console.error(e);
  } finally {
    if(browser) await browser.disconnect();
  }
})();
