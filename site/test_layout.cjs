// Run against the built site with Playwright and Chromium installed.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

async function check() {
  const browser = await chromium.launch({ headless: true });
  const url = process.argv[2] || 'http://127.0.0.1:8080';
  try {
    for (const width of [320, 375, 620, 621, 1440]) {
      const page = await browser.newPage({
        viewport: { width, height: 900 }, reducedMotion: 'reduce',
      });
      await page.goto(url);
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
        .every(video => video.readyState >= 2));
      await page.locator('#films').evaluate(element => element.scrollIntoView());
      const layout = await page.evaluate(() => {
        const rect = element => element.getBoundingClientRect().toJSON();
        return {
          scrollWidth: document.documentElement.scrollWidth,
          videos: [...document.querySelectorAll('#films video')].map(rect),
          details: [...document.querySelectorAll('#films .film-description')].map(rect),
          overflow: [...document.querySelectorAll('#films *')]
            .filter(element => element.scrollWidth > element.clientWidth + 1)
            .map(element => element.className || element.tagName),
        };
      });
      assert.equal(layout.scrollWidth, width, 'page must not overflow');
      assert.deepEqual(layout.overflow, [], 'comparison content must fit');
      const [wide, narrow] = layout.videos;
      assert.ok(Math.abs(wide.y - narrow.y) < 1, 'frames must align');
      assert.ok(wide.right < narrow.x, 'videos must be side by side');
      for (const video of layout.videos) {
        assert.ok(video.y >= 0 && video.bottom <= 900, 'both frames must be visible');
        assert.ok(Math.abs(video.width / video.height - 16 / 9) < 0.03);
      }
      assert.ok(layout.details.every(detail => detail.y >= Math.max(wide.bottom, narrow.bottom)),
        'descriptions must follow both videos');
      assert.deepEqual(await page.locator('#films .film-heading h2').allTextContents(),
        ['01 Wide', '02 Narrow']);
      assert.ok(await page.locator('#films video').evaluateAll(videos =>
        videos.length === 2 && videos.every(video => video.paused && video.controls && video.loop)),
      'reduced-motion startup must be paused with individual controls and looping');

      await page.locator('#play-both').click();
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
        .every(video => !video.paused && video.currentTime > 0.1));
      await page.locator('#play-both').click();
      assert.ok(await page.locator('#films video').evaluateAll(videos => videos.every(video => video.paused)));
      await page.locator('#films video').evaluateAll(videos => videos.forEach(video => { video.currentTime = 8; }));
      await page.locator('#replay-both').click();
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
        .every(video => !video.paused && video.currentTime < 2));
      await page.locator('#play-both').click();

      // Exercise Chromium's native play/pause button, independently of the paired controls.
      await page.locator('#wide-video').scrollIntoViewIfNeeded();
      const box = await page.locator('#wide-video').boundingBox();
      await page.mouse.click(box.x + 25, box.y + box.height - 50);
      await page.waitForFunction(() => !document.querySelector('#wide-video').paused);
      assert.ok(await page.locator('#narrow-video').evaluate(video => video.paused));
      await page.mouse.click(box.x + 25, box.y + box.height - 50);
      await page.waitForFunction(() => document.querySelector('#wide-video').paused);
      const links = await page.locator('#films .file-link').evaluateAll(elements => elements.map(element => element.href));
      assert.equal(links.length, 2);
      for (const link of links) {
        const response = await page.request.get(link);
        assert.ok(response.ok());
        assert.match(response.headers()['content-type'], /video\/mp4/);
      }
      console.log(`PASS ${width}px: layout, reduced motion, paired and native playback, MP4 links`);
      await page.close();
    }
    const page = await browser.newPage({ reducedMotion: 'no-preference' });
    await page.goto(url);
    await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
      .every(video => !video.paused && video.currentTime > 0));
    console.log('PASS default motion: both primary videos autoplay');
  } finally {
    await browser.close();
  }
}

check().catch(error => { console.error(error); process.exitCode = 1; });
