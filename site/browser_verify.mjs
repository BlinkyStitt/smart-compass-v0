import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {chromium} from 'playwright';
import {evaluate} from './energy.mjs';

const [url, directory] = process.argv.slice(2);
const expectedHTML = await readFile(resolve(directory, 'index.html'), 'utf8');
const expectedMovies = [...new Set([...expectedHTML.matchAll(/href="([^"]+\.mp4)"/g)]
  .map(match => new URL(match[1], url).href))].sort();
assert.ok(expectedMovies.length >= 3, 'Expected artifact must include primary and comparison MP4 links');
const model = JSON.parse(await readFile(resolve(directory, 'electrical-inputs.json'), 'utf8'));
const manifest = JSON.parse(await readFile(resolve(directory, 'pattern-samples.json'), 'utf8'));
const pin = JSON.parse(await readFile(new URL('./node_modules/playwright/package.json', import.meta.url), 'utf8'));
assert.equal(pin.version, '1.64.1');

async function expected(design, pattern, settings) {
  const set = manifest.sets.filter(row => row.design === design && row.pattern === pattern).sort((a, b) => b.steps - a.steps)[0];
  const bytes = await readFile(resolve(directory, 'pattern-data', set.file));
  const rgb = new Float32Array(bytes.length / 4);
  for (let i = 0; i < rgb.length; i++) rgb[i] = bytes.readFloatLE(i * 4);
  return evaluate({...set, rgb}, model.groups[design], settings);
}

async function settled(page) {
  await page.waitForFunction(() => document.querySelector('#energy-result')?.dataset.result
    && document.querySelector('#energy-calculator').getAttribute('aria-busy') === 'false');
  return JSON.parse(await page.locator('#energy-result').getAttribute('data-result'));
}

async function agreement(page) {
  const actual = await settled(page);
  const wanted = await expected(actual.design, actual.pattern, actual.settings);
  for (const key of ['average_led_a', 'sampled_peak_led_a', 'average_output_w', 'average_battery_w', 'usable_wh'])
    assert.ok(Math.abs(actual[key] - wanted[key]) < 1e-9, key);
  assert.equal(actual.runtime.state, wanted.runtime.state);
  assert.ok(Math.abs(actual.runtime.hours - wanted.runtime.hours) < 1e-9);
  assert.ok((await page.locator('#energy-result').innerText()).includes(wanted.runtime.hours.toFixed(2)));
  return actual;
}

// Use the pinned full Chromium runtime, including its media implementation.
// The separate headless shell does not complete this fixture on macOS.
const browser = await chromium.launch({headless: true, channel: 'chromium'});
try {
  for (const width of [320, 1280]) {
    const context = await browser.newContext({viewport: {width, height: 900}, reducedMotion: 'reduce'});
    try {
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      const initial = await agreement(page);
      assert.equal(initial.design, 'wide'); assert.equal(initial.pattern, 'rainbow');
      assert.ok((await page.locator('#energy-reference').innerText()).includes('2.45'));
      assert.equal(await page.locator('#energy-result').getAttribute('aria-live'), 'polite');
      assert.equal(await page.locator('#energy-error').getAttribute('role'), 'alert');
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Viewport overflow');
      await page.getByLabel('Design', {exact: true}).focus();
      await page.keyboard.press('Tab');
      assert.equal(await page.locator(':focus').getAttribute('name'), 'pattern');
      for (const design of ['wide', 'narrow']) {
        await page.getByLabel('Design', {exact: true}).selectOption(design);
        for (const pattern of ['rainbow', 'dark-sectors', 'dark-spirals', 'dark-diagonals']) {
          await page.getByLabel('Pattern', {exact: true}).selectOption(pattern);
          const changed = await agreement(page);
          assert.equal(changed.design, design); assert.equal(changed.pattern, pattern);
          if (pattern !== 'rainbow') assert.ok(changed.savings.watts > 0);
        }
      }
      // The selected dark pattern can be feasible while its rainbow baseline
      // is not. Keep its current/runtime visible without inventing savings.
      await page.getByLabel('Design', {exact: true}).selectOption('wide');
      await page.getByLabel('Pattern', {exact: true}).selectOption('dark-sectors');
      await page.getByLabel('Electrical brightness (%)', {exact: true}).fill('50');
      const comparison = await agreement(page);
      assert.equal(comparison.savings.state, 'unavailable');
      assert.equal(comparison.savings.watts, null);
      assert.equal(comparison.savings.percent, null);
      assert.ok(comparison.runtime.hours > 0);
      assert.ok((await page.locator('#energy-result').innerText()).includes('comparison unavailable'));
      assert.equal(await page.locator('#energy-error').innerText(), '');
      assert.equal(await page.getByLabel('Contact and wiring resistance (Ω)', {exact: true}).getAttribute('aria-invalid'), null);
      await page.getByRole('button', {name: 'Reset calculator'}).click();
      assert.equal((await agreement(page)).savings.state, 'available');
      for (const [label, value] of [['Electrical brightness (%)', '0'], ['Cell capacity (Ah)', '10.4'],
                                  ['Usable cell energy (Wh, after reserve)', '12'], ['Conversion efficiency (%)', '90'],
                                  ['Reserve and cutoff allowance (%)', '20'], ['Controller, sensors and radio output (W)', '0.3']]) {
        await page.getByLabel(label, {exact: true}).fill(value);
        const changed = await agreement(page);
        if (label.startsWith('Usable')) assert.ok(Math.abs(changed.usable_wh - 12) < 1e-9);
      }
      const black = await agreement(page);
      assert.ok(black.average_led_a > 0, 'Black must retain idle demand');
      await page.getByLabel('Cell capacity (Ah)', {exact: true}).fill('0');
      assert.equal((await agreement(page)).runtime.hours, 0);
      for (const invalid of ['0', '-1', '']) {
        await page.getByLabel('Conversion efficiency (%)', {exact: true}).fill(invalid);
        await page.waitForFunction(() => document.querySelector('#energy-error').textContent.includes('efficiency'));
        assert.equal(await page.locator('#energy-result').getAttribute('data-result'), null);
        assert.equal(await page.locator('#energy-result').isVisible(), false);
        assert.equal(await page.getByLabel('Conversion efficiency (%)', {exact: true}).getAttribute('aria-invalid'), 'true');
      }
      await page.getByRole('button', {name: 'Reset calculator'}).click();
      const reset = await agreement(page);
      assert.equal(reset.design, initial.design); assert.equal(reset.pattern, initial.pattern);
      assert.deepEqual(reset.settings, initial.settings);
      await page.getByLabel('Reserve and cutoff allowance (%)', {exact: true}).fill('100');
      assert.equal((await agreement(page)).runtime.hours, 0);
      await page.getByLabel('Usable cell energy (Wh, after reserve)', {exact: true}).fill('1');
      await page.waitForFunction(() => document.querySelector('#energy-error').textContent.includes('reserve'));
      assert.equal(await page.locator('#energy-result').getAttribute('data-result'), null);
      await page.getByRole('button', {name: 'Reset calculator'}).click();
      await agreement(page);
      assert.ok((await page.locator('#energy-video-note').innerText()).includes('fixed full-rainbow'));

      // A late response from a previous selection must never replace the current result.
      await page.evaluate(async () => {
        const {mountCalculator, loadSample} = await import('./calculator.js');
        const [model, manifest] = await Promise.all(['electrical-inputs.json', 'pattern-samples.json'].map(path => fetch(path).then(r => r.json())));
        window.studyRelease = null;
        window.studyOldFinished = false;
        mountCalculator(document.querySelector('#energy-calculator'), model, manifest, async set => {
          if (set.design === 'wide') await new Promise(resolve => { window.studyRelease = resolve; });
          const sample = await loadSample(set);
          if (set.design === 'wide') window.studyOldFinished = true;
          return sample;
        });
      });
      await page.waitForFunction(() => typeof window.studyRelease === 'function');
      await page.getByLabel('Design', {exact: true}).selectOption('narrow');
      assert.equal((await agreement(page)).design, 'narrow');
      await page.evaluate(() => window.studyRelease());
      await page.waitForFunction(() => window.studyOldFinished);
      assert.equal((await agreement(page)).design, 'narrow');

      // Exercise the shipped paired-player handlers with actual MP4 decoding.
      assert.ok(await page.locator('#films video').evaluateAll(videos => videos.every(video => video.paused)));
      await page.locator('#play-both').click();
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')].every(video => !video.paused && video.currentTime > 0));
      await page.locator('#films video').evaluateAll(videos => { videos[1].currentTime = videos[0].currentTime + .8; });
      await page.waitForFunction(() => { const v = document.querySelectorAll('#films video'); return Math.abs(v[0].currentTime - v[1].currentTime) < .15; });
      const beforeBuffer = await page.locator('#films video').last().evaluate(video => {
        Object.defineProperty(video, 'readyState', {configurable: true, value: 2});
        video.currentTime = document.querySelector('#films video').currentTime + .8;
        video.dispatchEvent(new Event('waiting'));
        return [...document.querySelectorAll('#films video')].map(v => ({time: v.currentTime, ready: v.readyState, seeking: v.seeking, paused: v.paused}));
      });
      // Wait two animation frames so the normal synchronizer observes buffering.
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const duringBuffer = await page.locator('#films video').evaluateAll(videos => videos.map(v => ({time: v.currentTime, ready: v.readyState, seeking: v.seeking, paused: v.paused})));
      assert.ok(Math.abs(duringBuffer[0].time - duringBuffer[1].time) > .15, JSON.stringify({beforeBuffer, duringBuffer}));
      await page.locator('#films video').last().evaluate(video => { delete video.readyState; video.dispatchEvent(new Event('canplay')); });
      await page.waitForFunction(() => { const v = document.querySelectorAll('#films video'); return Math.abs(v[0].currentTime - v[1].currentTime) < .15; });
      await page.locator('#play-both').click();
      assert.ok(await page.locator('#films video').evaluateAll(videos => videos.every(video => video.paused)));
      await page.locator('#films video').evaluateAll(videos => videos.forEach(video => { video.currentTime = 5; }));
      await page.locator('#replay-both').click();
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')].every(video => !video.paused && video.currentTime > 0 && video.currentTime < 2));
      await page.locator('#play-both').click();
      await page.locator('#films video').first().evaluate(video => { video.originalPlay = video.play; video.play = () => Promise.reject(new DOMException('fixture rejection', 'NotAllowedError')); });
      await page.locator('#play-both').click();
      await page.waitForFunction(() => document.querySelector('#play-status').textContent.includes('Playback did not start'));
      assert.ok(await page.locator('#films video').evaluateAll(videos => videos.every(video => video.paused)));
      await page.locator('#films video').first().evaluate(video => { video.play = video.originalPlay; video.dispatchEvent(new Event('error')); });
      assert.ok((await page.locator('#play-status').innerText()).includes('could not load'));
      const movies = [...new Set(await page.locator('a[href$=".mp4"]').evaluateAll(links => links.map(link => link.href)))].sort();
      assert.deepEqual(movies, expectedMovies, 'Every reviewed MP4 must retain its recovery link');
      for (const href of movies) {
        const response = await context.request.get(href);
        assert.equal(response.status(), 200);
        assert.ok((await response.body()).length > 1000);
      }
      assert.deepEqual(errors, []);
      console.log(`BROWSER PASS: ${width}px, design/pattern/settings/reset/keyboard/announcements/invalid/zero-energy, model agreement and playback recovery`);
    } finally { await context.close(); }
  }
  // Deliberately injected zero-demand coefficients test an otherwise unreachable
  // theoretical edge. This does not claim that black real LEDs consume no power.
  const zeroContext = await browser.newContext({reducedMotion: 'reduce'});
  try {
    const zero = structuredClone(model);
    zero.defaults.non_led_w = 0; zero.defaults.quiescent_w = 0;
    for (const groups of Object.values(zero.groups)) for (const group of groups) { group.idle_a = 0; group.channel_a = [0, 0, 0]; }
    await zeroContext.route('**/electrical-inputs.json', route => route.fulfill({json: zero}));
    const page = await zeroContext.newPage();
    await page.goto(url);
    const value = await settled(page);
    assert.equal(value.runtime.state, 'unbounded'); assert.equal(value.runtime.hours, null);
    assert.ok((await page.locator('#energy-result').innerText()).includes('no finite runtime'));
    assert.ok(!(await page.locator('#energy-result').innerText()).match(/NaN|Infinity/));
  } finally { await zeroContext.close(); }
  const damagedContext = await browser.newContext({reducedMotion: 'reduce'});
  try {
    await damagedContext.route('**/pattern-data/*.f32', route => route.fulfill({body: Buffer.from([0, 1, 2, 3])}));
    const page = await damagedContext.newPage();
    await page.goto(url);
    await page.waitForFunction(() => document.querySelector('#energy-error')?.textContent.includes('stale or damaged'));
    assert.equal(await page.locator('#energy-result').getAttribute('data-result'), null);
    assert.equal(await page.locator('#energy-result').isVisible(), false);
  } finally { await damagedContext.close(); }
  console.log(`BROWSER VERIFICATION COMPLETE: Playwright ${pin.version}, Chromium ${browser.version()}`);
} finally { await browser.close(); }
