const puppeteer = require('puppeteer-core');
const http = require('http');
async function getWsUrl() {
  return new Promise((resolve) => {
    http.get('http://172.20.0.2:9223/json/version', (res) => {
      let data = ''; res.on('data', (c) => data += c);
      res.on('end', () => resolve(JSON.parse(data).webSocketDebuggerUrl.replace('localhost', '172.20.0.2:9223')));
    });
  });
}
(async () => {
  const browser = await puppeteer.connect({ browserWSEndpoint: await getWsUrl() });
  const page = await browser.newPage();
  await page.goto('https://lms.ipexdesenvolvimento.cloud/login');
  await new Promise(r => setTimeout(r, 3000));
  const html = await page.content();
  console.log(html);
  await browser.disconnect();
})();
