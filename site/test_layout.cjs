const assert = require('node:assert/strict');
const {chromium, webkit} = require('playwright');
const engine = process.env.GALLERY_BROWSER || 'chromium';

async function assertViewportFit(media) {
  const size = await media.evaluate(async element => {
    if (element instanceof HTMLImageElement) await element.decode();
    const width = element.naturalWidth || element.videoWidth;
    const height = element.naturalHeight || element.videoHeight;
    const box = element.getBoundingClientRect();
    const fit = Math.min(box.width / width, box.height / height);
    const available = Math.min(innerWidth / width, innerHeight / height);
    return {paintedHeight: height * fit, availableHeight: height * available};
  });
  assert.ok(size.paintedHeight >= size.availableHeight - 1,
    `Media uses the available viewport (${size.paintedHeight}px of ${size.availableHeight}px)`);
}

async function check() {
  const browser = await (engine === 'webkit' ? webkit : chromium).launch({headless: true, ...(engine === 'webkit' ? {} : {channel: 'chromium'})});
  const url = process.argv[2] || 'http://127.0.0.1:8080';
  try {
    for (const width of [320, 390, 620, 1280, 1920]) {
      const context = await browser.newContext({viewport: {width, height: 900}, reducedMotion: 'reduce', hasTouch: width < 620});
      try {
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.route('**/app.js', route => route.fulfill({contentType: 'application/javascript', body: 'throw new Error("stale player script fixture")'}));
        await page.goto(url);
        assert.match(await page.locator('script[src*="app-"]').getAttribute('src'), /app-script-[0-9a-f]{12}\.js$/, 'Player script URL changes with its content');
        assert.equal(await page.locator('#films video').count(), 1);
        assert.equal(await page.locator('[id*=wide]').count(), 0);
        assert.ok(!(await page.locator('main').innerText()).match(/wide archive|wide design|compare sizes|play both/i));
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        const primary = await page.locator('#films video').boundingBox();
        assert.ok(primary.width >= Math.min(width - 40, 950), 'Primary narrow view uses the available width');
        await page.locator('#narrow-video').scrollIntoViewIfNeeded();
        await page.waitForFunction(() => { const v = document.querySelector('#narrow-video'); return !v.paused && v.currentTime > 0; });
        await page.emulateMedia({reducedMotion: 'no-preference'});
        await page.emulateMedia({reducedMotion: 'reduce'});
        assert.ok(await page.locator('#narrow-video').evaluate(v => !v.paused), 'Requested primary autoplay survives Reduce Motion');
        await page.waitForFunction(() => document.querySelector('#narrow-video').readyState >= 1);
        assert.equal(await page.locator('#narrow-video').evaluate(video => video.duration), 16,
          'First preview keeps one complete full-rainbow loop');
        const previewLabel = await page.locator('#narrow-video').getAttribute('aria-label');
        assert.match(previewLabel, /Pride rainbow chase, all sections lit/);
        if (width === 390) {
          await page.locator('#narrow-video').tap();
          const viewer = page.getByRole('dialog', {name: 'Full-screen media'});
          await viewer.waitFor({state: 'visible'});
          assert.ok(!(await viewer.innerText()).includes(previewLabel), 'The video description is not displayed as a caption');
          const video = viewer.locator('video');
          assert.equal(await video.getAttribute('aria-label'), previewLabel);
          await page.waitForFunction(() => document.querySelector('.media-viewer video').videoHeight > 0);
          assert.ok(await video.evaluate(v => !v.controls && v.loop), 'Native controls start hidden');
          await assertViewportFit(video);

          // Keep the video open during rotation and expose native controls only on request.
          await page.setViewportSize({width: 844, height: 390});
          await assertViewportFit(video);
          const close = viewer.getByRole('button', {name: 'Close full-screen media'});
          assert.equal(await close.innerText(), '×');
          const box = await close.boundingBox();
          assert.ok(box.width >= 44 && box.height >= 44 && box.y >= 0 && box.y <= 24 &&
            box.x + box.width <= 844 && box.x + box.width >= 820,
          'Close floats in the top-right corner with a touch target of at least 44px');

          const controls = viewer.getByRole('button', {name: 'Playback controls'});
          await page.keyboard.press('Tab');
          assert.ok(await controls.evaluate(button => button === document.activeElement));
          await page.keyboard.press('Space');
          assert.equal(await controls.getAttribute('aria-pressed'), 'true');
          assert.ok(await video.evaluate(v => v.controls));
          await assertViewportFit(video);
          await controls.tap();
          assert.equal(await controls.getAttribute('aria-pressed'), 'false');
          assert.ok(await video.evaluate(v => !v.controls));
          await close.tap();
          await page.setViewportSize({width, height: 900});
          await viewer.waitFor({state: 'hidden'});
        }

        // Every bounded still preview opens in place.
        const links = page.locator('main a:has(img)');
        assert.equal(await links.count(), 4);
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
          assert.equal(await dialog.locator('img').getAttribute('alt'), await link.locator('img').getAttribute('alt'));
          assert.ok(await dialog.getByRole('button', {name: 'Close full-screen media'}).evaluate(button => button === document.activeElement));
          if (i % 2) await page.keyboard.press('Escape');
          else await dialog.getByRole('button', {name: 'Close full-screen media'}).click();
          await dialog.waitFor({state: 'hidden'});
          assert.ok(await link.evaluate(element => element === document.activeElement), 'Focus returns to the image');
        }

        // The assembly starts without a tap, including with reduced motion enabled.
        const assembly = page.locator('[data-assembly]');
        await assembly.scrollIntoViewIfNeeded();
        await page.waitForFunction(() => { const v = document.querySelector('#assembly-video'); return !v.paused && v.currentTime > 0; });
        await page.emulateMedia({reducedMotion: 'no-preference'});
        await page.emulateMedia({reducedMotion: 'reduce'});
        assert.ok(await assembly.locator('video').evaluate(v => !v.paused), 'The requested assembly autoplay survives motion-preference changes');
        assert.equal(await assembly.locator('video').evaluate(v => v.duration), 48, 'Complete disassembly includes every fitted-part detail view');
        await assembly.locator('video').click();
        await page.getByRole('dialog').waitFor({state: 'visible'});
        assert.ok(await assembly.locator('video').evaluate(v => v.paused));
        await page.waitForFunction(() => { const v = document.querySelector('.media-viewer video'); return !v.paused && v.currentTime > 0; });
        const expanded = await page.getByRole('dialog').locator('video').elementHandle();
        await page.getByRole('button', {name: 'Close full-screen media'}).click();
        await page.waitForFunction(() => !document.querySelector('#assembly-video').paused);
        assert.ok(await expanded.evaluate(v => !v.hasAttribute('src') && v.readyState === 0), 'Closing releases the full-screen decoder');
        await assembly.locator('[data-play]').click();
        assert.ok(await assembly.locator('video').evaluate(v => v.paused));

        // A browser that denies native fullscreen still gets a full viewport dialog.
        await page.evaluate(() => { HTMLDialogElement.prototype.requestFullscreen = () => Promise.reject(new Error('Fixture: fullscreen unavailable')); });
        await links.first().focus();
        await page.keyboard.press('Enter');
        const fallback = page.getByRole('dialog');
        await fallback.waitFor({state: 'visible'});
        if (width === 390) {
          // Keep the image open while a phone rotates into landscape.
          await page.setViewportSize({width: 844, height: 390});
          await assertViewportFit(fallback.locator('img'));
          assert.equal(await fallback.getByRole('button', {name: 'Playback controls'}).count(), 0);
          const close = await fallback.getByRole('button', {name: 'Close full-screen media'}).boundingBox();
          assert.ok(close.x >= 0 && close.y >= 0 && close.x + close.width <= 844 && close.y + close.height <= 390,
            'Close stays within the rotated viewport');
          await page.setViewportSize({width, height: 900});
        }
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
          assert.ok(await page.getByRole('dialog').locator('video').evaluate(v => !v.controls && v.loop));
          await page.getByRole('button', {name: 'Close full-screen media'}).click();
          await page.waitForFunction(id => !document.querySelector(`#${id} video`).paused, id);
          await details.locator('summary').click();
          await page.waitForFunction(id => document.querySelector(`#${id} video`).paused, id);
        }
        assert.deepEqual(errors, []);
        console.log(`GALLERY PASS: ${width}px, narrow only, image/video fullscreen, touch/keyboard/focus, reduced motion, pattern playback`);
      } finally { await context.close(); }
    }
    // Both requested animations start without JavaScript or a priming tap.
    const native = await browser.newContext({javaScriptEnabled: false, reducedMotion: 'reduce', viewport: {width: 390, height: 844}});
    try {
      const page = await native.newPage();
      await page.goto(url);
      for (const id of ['narrow-video', 'assembly-video']) {
        await page.locator(`#${id}`).scrollIntoViewIfNeeded();
        // Page-side timer/rAF polling is disabled in this context too.
        let moving = false;
        for (let attempt = 0; attempt < 150 && !moving; attempt++) {
          moving = await page.locator(`#${id}`).evaluate(v => v.autoplay && v.muted && v.playsInline && !v.paused && v.currentTime > 0);
          if (!moving) await new Promise(resolve => setTimeout(resolve, 100));
        }
        assert.ok(moving, `${id} native autoplay advances without a script or tap`);
      }
      console.log(`NATIVE AUTOPLAY PASS (${engine}): both muted inline videos start without JavaScript or a tap`);
    } finally { await native.close(); }
    const recovery = await browser.newContext({reducedMotion: 'reduce', viewport: {width: 390, height: 844}, hasTouch: true});
    try {
      await recovery.addInitScript(() => {
        const add = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, handler, options) {
          if (type === 'click' && this instanceof Element && this.hasAttribute('data-play') && typeof handler === 'function') {
            const button = this, original = handler;
            handler = function(event) {
              const v = button.closest('[data-player]').querySelector('video');
              v.inClick = true;
              try { return original.call(this, event); } finally { v.inClick = false; }
            };
          }
          return add.call(this, type, handler, options);
        };
      });
      const page = await recovery.newPage();
      await page.goto(url);
      for (const id of ['narrow-video', 'assembly-video']) {
        const video = page.locator(`#${id}`);
        await video.scrollIntoViewIfNeeded();
        await page.waitForFunction(id => !document.getElementById(id).paused, id);
        await video.evaluate(v => {
          v.autoplay = false;
          v.pause();
          v.originalPlay = v.play;
          v.play = () => Promise.reject(new DOMException('Autoplay policy fixture', 'NotAllowedError'));
          document.dispatchEvent(new Event('visibilitychange'));
        });
        const player = video.locator('xpath=ancestor::*[@data-player][1]');
        await page.waitForFunction(id => document.getElementById(id).closest('[data-player]').querySelector('.play-status').textContent.includes('Tap Play'), id);
        await video.evaluate(v => { v.play = v.originalPlay; v.dispatchEvent(new Event('canplay')); });
        await page.waitForFunction(id => { const v = document.getElementById(id); return !v.paused && v.currentTime > 0; }, id);
        await player.locator('[data-play]').click();
        assert.ok(await video.evaluate(v => v.paused));
        // A button retry must call play() before the gesture handler returns.
        await video.evaluate(v => {
          v.play = function() { this.playWasInClick = this.inClick; return this.originalPlay(); };
        });
        await player.locator('[data-play]').click();
        await page.waitForFunction(id => !document.getElementById(id).paused, id);
        assert.ok(await video.evaluate(v => v.playWasInClick), 'Play stays inside the Safari user gesture');
        await video.evaluate(v => { v.play = v.originalPlay; });
      }
      console.log(`AUTOPLAY RECOVERY PASS (${engine}): both videos retry a denied start and retain synchronous Play`);
    } finally { await recovery.close(); }
    const context = await browser.newContext({reducedMotion: 'no-preference'});
    try {
      const page = await context.newPage();
      const requests = [];
      const errors = [];
      page.on('request', request => requests.push(request.url()));
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()}: ${response.url()}`); });
      await page.goto(url);
      await page.waitForFunction(() => { const v = document.querySelector('#films video'); return !v.paused && v.currentTime > 0; });
      const assembly = page.locator('#assembly-video');
      await assembly.scrollIntoViewIfNeeded();
      await page.waitForFunction(() => document.querySelector('#narrow-video').paused && !document.querySelector('#assembly-video').paused && document.querySelector('#assembly-video').currentTime > 0);
      const first = await assembly.screenshot();
      await page.waitForTimeout(4000);
      const opened = await assembly.screenshot();
      assert.ok(!first.equals(opened), 'Exploded video changes its painted CAD pose');
      await page.locator('[data-assembly] [data-play]').click();
      for (let repeat = 0; repeat < 2; repeat++) {
        for (const image of await page.locator('main img').all()) {
          await image.scrollIntoViewIfNeeded();
          await image.evaluate(i => i.decode());
          const dimensions = await image.evaluate(i => [i.naturalWidth, i.naturalHeight]);
          assert.ok(dimensions.every(n => n > 0 && n <= 1600), 'Inline images have bounded decoded dimensions');
        }
        await assembly.scrollIntoViewIfNeeded();
        assert.ok(await assembly.evaluate(v => v.paused), 'Manual pause survives scrolling away and back');
      }
      assert.ok(!requests.some(url => /\.(svg|apng)(?:[?#]|$)/.test(url) && !url.endsWith('/icon.svg')), 'Scrolling never loads tessellated SVGs or animated PNGs');
      assert.equal(await page.locator('img[src$=".svg"],img[src$=".apng"]').count(), 0);
      await page.locator('#narrow-video').scrollIntoViewIfNeeded();
      await page.waitForFunction(() => !document.querySelector('#narrow-video').paused);
      // Synthetic visibility transition exercises the browser lifecycle event.
      await page.evaluate(() => {
        Object.defineProperty(document, 'hidden', {configurable: true, value: true});
        document.dispatchEvent(new Event('visibilitychange'));
      });
      assert.ok(await page.locator('#narrow-video').evaluate(v => v.paused));
      await page.evaluate(() => {
        delete document.hidden;
        document.dispatchEvent(new Event('visibilitychange'));
      });
      await page.waitForFunction(() => !document.querySelector('#narrow-video').paused);
      await page.emulateMedia({reducedMotion: 'reduce'});
      assert.ok(await page.locator('#narrow-video').evaluate(v => !v.paused), 'Requested primary autoplay overrides Reduce Motion');
      await page.locator('#play').click();
      await page.evaluate(() => {
        document.querySelector('#narrow-video').dispatchEvent(new Event('canplay'));
        window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}));
      });
      assert.ok(await page.locator('#narrow-video').evaluate(v => v.paused), 'Manual pause survives media-ready and page-return retries');
      assert.deepEqual(errors, []);
      console.log(`MOTION/MEMORY PASS (${engine}): painted assembly motion, bounded images, repeated scroll, offscreen pause/resume, manual pause, visibility and reduced motion`);
    } finally { await context.close(); }
  } finally { await browser.close(); }
}
check().catch(error => { console.error(error); process.exitCode = 1; });
