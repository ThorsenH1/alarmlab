const {chromium} = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');

(async () => {
  const root = path.resolve(__dirname, '..');
  const browser = await chromium.launch({
    ...(process.env.ALARMLAB_BROWSER ? {executablePath: process.env.ALARMLAB_BROWSER} : {}),
    headless: true
  });
  const page = await browser.newPage({viewport: {width: 1440, height: 1100}});
  const errors = [], network = [], checks = [];
  page.on('pageerror', error => errors.push(String(error)));
  page.on('request', request => { if (/^https?:/.test(request.url())) network.push(request.url()); });
  await page.goto(pathToFileURL(path.join(root, 'demo/index.html')).href);
  await page.waitForSelector('#sensor-cards button');
  assert.match(await page.locator('#status').innerText(), /Avvik/);
  checks.push('Default trace loads with real precomputed alarm state');
  await page.screenshot({path: path.join(root, 'demo/preview-desktop.png'), fullPage: true});
  for (const domain of ['in_domain', 'noise_shift', 'context_shift']) {
    await page.selectOption('#domain', domain);
    for (const scenario of ['normal','load_step','pump_wear','cooling_loss','sensor_bias','dropout','stuck_sensor']) {
      await page.selectOption('#scenario', scenario);
      for (const model of ['contextual_residual','isolation_forest','raw_limits']) {
        await page.selectOption('#model', model);
        await page.locator('#time').evaluate(el => { el.value = '500'; el.dispatchEvent(new Event('input', {bubbles:true})); });
        const result = await page.evaluate(() => {
          const t = window.ALARMLAB_DATA.traces.find(t => t.scenario === document.querySelector('#scenario').value && t.domain === document.querySelector('#domain').value);
          return {expected:t.methods[document.querySelector('#model').value].states[500], text:document.querySelector('#status').textContent};
        });
        const label = {REVIEW:/utilgjengelig/, ALARM:/Avvik/, NORMAL:/Ingen vedvarende/, WATCH:/Følg med/, WARMUP:/historikk/}[result.expected];
        assert(label, 'Unknown Python state');
        assert.match(result.text, label);
      }
    }
  }
  checks.push('All 63 scenario/domain/model combinations match Python states at t=1000 s');
  await page.selectOption('#domain', 'in_domain');
  await page.selectOption('#scenario', 'dropout');
  assert.equal(await page.locator('#score-value').innerText(), 'Ingen skår');
  await page.check('#truth');
  assert.equal(await page.locator('#truth-caption').isVisible(), true);
  checks.push('Missing data suppresses the score; truth overlay is opt-in');
  await page.fill('#note', 'Browser verification: quality issue.');
  await page.click('#log');
  assert.match(await page.locator('#log-message').innerText(), /Lagret lokalt/);
  const downloadPromise = page.waitForEvent('download');
  await page.click('#export-log');
  const download = await downloadPromise;
  const logPath = path.join(root, 'work/browser-export.json');
  fs.mkdirSync(path.dirname(logPath), {recursive:true});
  await download.saveAs(logPath);
  const log = JSON.parse(fs.readFileSync(logPath, 'utf8'));
  assert.equal(log.entries.at(-1).scenario, 'dropout');
  assert.equal(log.entries.at(-1).model_status, 'REVIEW');
  checks.push('Local human assessment is persisted and exported with data fingerprint');
  await page.click('[data-tab="results"]');
  assert.equal(await page.locator('#results-table tbody tr').count(), 3);
  await page.selectOption('#results-domain', 'noise_shift');
  await page.screenshot({path: path.join(root, 'demo/preview-stress-test.png'), fullPage: true});
  await page.click('[data-tab="real"]');
  await page.selectOption('#real-task', 'pump_leakage');
  assert.equal(await page.locator('#real-table tbody tr').count(), 3);
  await page.click('[data-tab="method"]');
  assert.match(await page.locator('#provenance').innerText(), /SHA-256/);
  checks.push('Experiment, real-data and methodology views render');
  await page.click('[data-tab="operator"]');
  await page.selectOption('#scenario', 'pump_wear');
  await page.selectOption('#model', 'contextual_residual');
  await page.uncheck('#truth');
  await page.click('#restart');
  assert.match(await page.locator('#status').innerText(), /historikk/);
  const initial = await page.locator('#time').inputValue();
  await page.click('#play');
  await page.waitForTimeout(650);
  await page.click('#play');
  assert(Number(await page.locator('#time').inputValue()) > Number(initial));
  checks.push('Restart, warmup and playback controls work');
  await page.setViewportSize({width:390,height:844});
  await page.locator('#time').evaluate(el => {el.value = '350'; el.dispatchEvent(new Event('input', {bubbles:true}));});
  await page.screenshot({path:path.join(root,'demo/preview-mobile.png'),fullPage:true});
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  for (const tab of ['results', 'real', 'method', 'operator']) {
    await page.click('[data-tab="' + tab + '"]');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), 'Overflow in mobile ' + tab);
  }
  checks.push('Mobile viewport has no horizontal overflow');
  assert.equal(errors.length, 0, errors.join('\n'));
  assert.equal(network.length, 0, 'Offline demo unexpectedly requested network');
  checks.push('No browser exceptions and no network requests');
  fs.writeFileSync(path.join(root, 'artifacts/browser_verification.json'), JSON.stringify({
    browser: await browser.version(), desktop_viewport:[1440,1100],mobile_viewport:[390,844],
    checks, errors, network_requests:network
  },null,2));
  console.log(JSON.stringify({checks:checks.length,errors,network_requests:network},null,2));
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
