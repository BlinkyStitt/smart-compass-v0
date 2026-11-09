const assert = require('node:assert/strict');
const {chromium} = require('playwright');

async function check() {
  const browser = await chromium.launch({headless: true, channel: 'chromium'});
  const url = process.argv[2] || 'http://127.0.0.1:8080';
  try {
    for (const width of [320, 390, 620, 1280, 1920]) {
      const context = await browser.newContext({viewport: {width, height: 900}, reducedMotion: 'reduce', hasTouch: width < 620});
      try {
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(url);
        assert.equal(await page.locator('#films video').count(), 1);
        assert.equal(await page.locator('[id*=wide]').count(), 0);
        assert.ok(!(await page.locator('main').innerText()).match(/wide archive|wide design|compare sizes|play both/i));
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        const primary = await page.locator('#films video').boundingBox();
        assert.ok(primary.width >= Math.min(width - 40, 950), 'Primary narrow view uses the available width');
        assert.ok(await page.locator('#films video').evaluate(video => video.paused));

        // Every still and the animated diagram opens in place, including SVGs.
        const links = page.locator('main a:has(img)');
        assert.equal(await links.count(), 5);
        for (let i = 0; i < await links.count(); i++) {
          const link = links.nth(i);
          const href = page.url();
          if (width < 620) await link.tap(); else await link.click();
          const dialog = page.getByRole('dialog', {name: 'Full-screen media'});
          await dialog.waitFor({state: 'visible'});
          await page.waitForFunction(() => { const i = document.querySelector('.media-viewer img'); return i?.complete && i.naturalWidth > 0; });
          const box = await dialog.boundingBox();
          assert.ok(box.width >= width && box.height >= 900, 'Viewer fills the viewport');
          assert.equal(page.url(), href, 'Image tap keeps the page in place');
          assert.ok(await dialog.getByRole('button', {name: 'Close ×'}).evaluate(button => button === document.activeElement));
          if (i % 2) await page.keyboard.press('Escape');
          else await dialog.getByRole('button', {name: 'Close ×'}).click();
          await dialog.waitFor({state: 'hidden'});
          assert.ok(await link.evaluate(element => element === document.activeElement), 'Focus returns to the image');
        }

        // Reduced motion uses a still. Explicit playback and pause remain available.
        const image = page.locator('#assembly-image');
        assert.ok((await image.evaluate(i => i.currentSrc)).endsWith('.jpg'));
        await page.getByRole('button', {name: 'Play animation', exact: true}).click();
        await page.waitForFunction(() => document.querySelector('#assembly-image').currentSrc.endsWith('.apng'));
        await page.getByRole('button', {name: 'Pause animation', exact: true}).click();
        await page.waitForFunction(() => document.querySelector('#assembly-image').currentSrc.endsWith('.jpg'));

        // A browser that denies native fullscreen still gets a full viewport dialog.
        await page.evaluate(() => { HTMLDialogElement.prototype.requestFullscreen = () => Promise.reject(new Error('Fixture: fullscreen unavailable')); });
        await links.first().focus();
        await page.keyboard.press('Enter');
        await page.getByRole('dialog').waitFor({state: 'visible'});
        await page.keyboard.press('Tab');
        assert.ok(await page.getByRole('dialog').evaluate(d => d.contains(document.activeElement)), 'Focus stays inside the viewer');
        await page.keyboard.press('Escape');
        await page.getByRole('dialog').waitFor({state: 'hidden'});

        for (const id of ['dark-sectors', 'dark-spirals', 'dark-diagonals', 'silver-rings']) {
          const details = page.locator(`#${id}`);
          await details.locator('summary').click();
          assert.equal(await details.locator('video').count(), 1);
          assert.ok(await details.locator('video').evaluate(v => v.paused));
          await details.locator('[data-play]').click();
          await page.waitForFunction(id => { const v = document.querySelector(`#${id} video`); return !v.paused && v.currentTime > 0; }, id);
          await details.locator('.media-expand').click();
          await page.getByRole('dialog').waitFor({state: 'visible'});
          assert.ok(await details.locator('video').evaluate(v => v.paused));
          assert.ok(await page.getByRole('dialog').locator('video').evaluate(v => v.controls && v.loop));
          await page.getByRole('button', {name: 'Close ×'}).click();
          await page.waitForFunction(id => !document.querySelector(`#${id} video`).paused, id);
          await details.locator('summary').click();
          await page.waitForFunction(id => document.querySelector(`#${id} video`).paused, id);
        }
        assert.deepEqual(errors, []);
        console.log(`GALLERY PASS: ${width}px, narrow only, image/video fullscreen, touch/keyboard/focus, reduced motion, pattern playback`);
      } finally { await context.close(); }
    }
    const context = await browser.newContext({reducedMotion: 'no-preference'});
    try {
      const page = await context.newPage();
      await page.goto(url);
      await page.waitForFunction(() => { const v = document.querySelector('#films video'); return !v.paused && v.currentTime > 0; });
      await page.locator('#assembly-image').scrollIntoViewIfNeeded();
      await page.waitForFunction(() => { const i = document.querySelector('#assembly-image'); return i.complete && i.currentSrc.endsWith('.apng') && i.naturalWidth > 0; });
      // Canvas drawImage uses an animated image's default frame. Compare the
      // browser's painted image instead so this check observes actual motion.
      const first = await page.locator('#assembly-image').screenshot();
      await page.waitForTimeout(4000);
      const opened = await page.locator('#assembly-image').screenshot();
      assert.ok(!first.equals(opened), 'Animated image changes its rendered CAD pose');
      await page.emulateMedia({reducedMotion: 'reduce'});
      await page.waitForFunction(() => document.querySelector('#films video').paused && document.querySelector('#assembly-image').currentSrc.endsWith('.jpg'));
      console.log('MOTION PASS: autoplay, decoded animated image motion, dynamic reduced-motion preference');
    } finally { await context.close(); }
  } finally { await browser.close(); }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
