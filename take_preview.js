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
async function runTest(role, email, password) {
  let browser;
  try {
    const ws = await getWsUrl();
    browser = await puppeteer.connect({ browserWSEndpoint: ws });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });
    
    console.log(`Testando ${role}...`);
    await page.goto('https://lms.ipexdesenvolvimento.cloud/api/method/logout');
    await page.goto('https://lms.ipexdesenvolvimento.cloud/login');
    
    await page.waitForSelector('#login_email');
    await page.type('#login_email', email);
    await page.type('#login_password', password);
    await page.click('.btn-login');
    await page.waitForNavigation({ waitUntil: 'networkidle2' });

    await page.goto('https://lms.ipexdesenvolvimento.cloud/lms');
    await new Promise(r => setTimeout(r, 10000));
    await page.screenshot({ path: `/root/projeto-tds/preview_${role}.png` });
    console.log(`Finalizado: ${role}`);
    await page.close();
  } catch (e) { console.error(e); }
  finally { if(browser) await browser.disconnect(); }
}
(async () => {
  await runTest('aluno', 'aluno_teste@ipex.edu', 'teste123');
  await runTest('professor', 'professor_teste@ipex.edu', 'teste123');
  await runTest('gestor', 'gestor_teste@ipex.edu', 'teste123');
})();
