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
    
    const sidebarClasses = await page.evaluate(() => {
      const sb = document.querySelector('.bg-surface-menu-bar');
      return sb ? sb.className : 'Not found';
    });
    console.log('Sidebar classes:', sidebarClasses);

    const computedStyles = await page.evaluate(() => {
      const sb = document.querySelector('.bg-surface-menu-bar');
      if (!sb) return null;
      const styles = window.getComputedStyle(sb);
      return {
        backgroundColor: styles.backgroundColor,
      };
    });
    console.log('Sidebar Computed Styles:', computedStyles);
    
    // Dump the style tags in head to see where Tailwind variables are
    const styleTags = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('style')).map(s => s.innerText.substring(0, 100));
    });
    console.log('Style tags:', styleTags);
    
    await page.close();
  } catch(e) { console.error(e); }
  finally { if(browser) browser.disconnect(); }
})();
