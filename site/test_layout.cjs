// Run against the built site with Playwright and Chromium installed.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

async function check() {
  const browser = await chromium.launch({ headless: true });
  const url = process.argv[2] || 'http://127.0.0.1:8080';
  const names = ['Rainbow • dark sectors', 'Rainbow • dark spirals',
    'Rainbow • dark diagonals', 'Silver PETG rings'];
  try {
    for (const width of [320, 375, 620, 621, 1440, 1600, 1920]) {
      const page = await browser.newPage({
        viewport: { width, height: 900 }, reducedMotion: 'reduce',
      });
      await page.goto(url);
      await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
        .every(video => video.readyState >= 2));
      const introduction = await page.evaluate(() => {
        const rect = element => element.getBoundingClientRect().toJSON();
        return {
          blocks: [...document.querySelector('.intro').children].map(rect),
          subtitle: rect(document.querySelector('.intro .lede')),
          films: rect(document.querySelector('#films')),
          story: rect(document.querySelector('.story-copy')),
          largeCopy: document.querySelector('.story-copy .large') !== null,
        };
      });
      assert.equal(introduction.blocks.length, 3, 'only status, headline and subtitle precede the videos');
      for (let index = 1; index < introduction.blocks.length; index++) {
        assert.ok(introduction.blocks[index].y >= introduction.blocks[index - 1].bottom,
          'introduction must stay vertically stacked at every width');
      }
      assert.ok(introduction.subtitle.bottom <= introduction.films.y,
        'short introduction must precede the comparison');
      assert.ok(introduction.largeCopy && introduction.story.y >= introduction.films.bottom,
        'large explanation must follow the comparison');
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
        videos.length === 2 && videos.every(video => video.paused && !video.controls && video.loop)),
      'reduced-motion startup must be paused and looping without browser controls');

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

      assert.ok(await page.locator('video').evaluateAll((videos, pairs) =>
        videos.length === 3 + pairs * 2 && videos.every(video => !video.controls), names.length),
      'all inline videos must hide browser player controls');
      const links = await page.locator('#films .file-link').evaluateAll(elements => elements.map(element => element.href));
      assert.equal(links.length, 2);
      for (const link of links) {
        const response = await page.request.get(link);
        assert.ok(response.ok());
        assert.match(response.headers()['content-type'], /video\/mp4/);
      }
      const disclosures = page.locator('details[data-comparison]');
      assert.deepEqual(await disclosures.locator('summary').allTextContents(), names);
      assert.ok(await disclosures.evaluateAll(items => items.every(item =>
        !item.open && [...item.querySelectorAll('video')].every(video => video.paused))),
      'all disclosures start closed and paused');
      for (let index = 0; index < names.length; index++) {
        const disclosure = disclosures.nth(index);
        const summary = disclosure.locator('summary');
        await summary.focus();
        await page.keyboard.press('Enter');
        await page.waitForFunction(i => document.querySelectorAll('details[data-comparison]')[i].open, index);
        assert.ok(await disclosure.locator('video').evaluateAll(videos => videos.every(video => video.paused)),
          'opening respects reduced motion');
        assert.deepEqual(await disclosure.locator('h3').allTextContents(), ['Wide', 'Narrow']);
        const frames = await disclosure.locator('video').evaluateAll(videos => videos.map(video => {
          return video.getBoundingClientRect().toJSON();
        }));
        if (width <= 620) assert.ok(frames[1].y >= frames[0].bottom, 'narrow layouts stack');
        else {
          assert.ok(Math.abs(frames[0].y - frames[1].y) < 1, 'wide layouts align');
          assert.ok(frames[1].x >= frames[0].right, 'wide layouts have two columns');
        }
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), width);
        const play = disclosure.locator('[data-play-both]');
        await play.click();
        await page.waitForFunction(i => [...document.querySelectorAll('details[data-comparison]')[i]
          .querySelectorAll('video')].every(video => !video.paused && video.currentTime > .1), index);
        await disclosure.locator('video').nth(1).evaluate(video => { video.currentTime = 7; });
        await page.waitForFunction(i => {
          const [a, b] = document.querySelectorAll('details[data-comparison]')[i].querySelectorAll('video');
          return Math.abs(a.currentTime - b.currentTime) < .15;
        }, index);
        assert.ok(await page.locator('details[data-comparison]').evaluateAll((items, selected) =>
          items.every((item, i) => i === selected || [...item.querySelectorAll('video')]
            .every(video => video.paused)), index), 'controls affect only their pair');
        await play.click();
        assert.ok(await disclosure.locator('video').evaluateAll(videos => videos.every(video => video.paused)));
        await disclosure.locator('video').evaluateAll(videos => videos.forEach(video => { video.currentTime = 8; }));
        await disclosure.locator('[data-replay-both]').click();
        await page.waitForFunction(i => [...document.querySelectorAll('details[data-comparison]')[i]
          .querySelectorAll('video')].every(video => !video.paused && video.currentTime < 2), index);
        for (const link of await disclosure.locator('.file-link').evaluateAll(links => links.map(a => a.href))) {
          const response = await page.request.get(link);
          assert.ok(response.ok());
          assert.match(response.headers()['content-type'], /video\/mp4/);
          assert.match(link, /-[a-f0-9]{12}\.mp4$/);
        }
        for (const video of await disclosure.locator('video').evaluateAll(videos => videos.map(video =>
          ({ poster: video.poster, label: video.getAttribute('aria-label') })))) {
          assert.ok(video.label);
          assert.match(video.poster, /-[a-f0-9]{12}\.jpg$/);
          assert.ok((await page.request.get(video.poster)).ok());
        }
        await summary.focus();
        await page.keyboard.press('Space');
        await page.waitForFunction(i => {
          const item = document.querySelectorAll('details[data-comparison]')[i];
          return !item.open && [...item.querySelectorAll('video')].every(video => video.paused);
        }, index);
      }
      console.log(`PASS ${width}px: stacked introduction, layout, reduced motion, paired playback, hidden browser controls, MP4 links`);
      await page.close();
    }
    const page = await browser.newPage({ reducedMotion: 'no-preference' });
    await page.goto(url);
    await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
      .every(video => !video.paused && video.currentTime > 0));
    for (let index = 0; index < names.length; index++) {
      const disclosure = page.locator('details[data-comparison]').nth(index);
      await disclosure.locator('summary').click();
      await page.waitForFunction(i => [...document.querySelectorAll('details[data-comparison]')[i]
        .querySelectorAll('video')].every(video => !video.paused && video.currentTime > .1), index);
      await disclosure.locator('summary').click();
      await page.waitForFunction(i => [...document.querySelectorAll('details[data-comparison]')[i]
        .querySelectorAll('video')].every(video => video.paused), index);
    }
    // Hold play() completions until after the disclosure's close handler ran.
    await page.evaluate(() => {
      const play = HTMLMediaElement.prototype.play;
      window.releasePlayback = [];
      HTMLMediaElement.prototype.play = function () {
        const result = play.call(this);
        return this.closest('details') ? result.then(() => new Promise(resolve =>
          window.releasePlayback.push(resolve))) : result;
      };
    });
    const first = page.locator('details[data-comparison]').first();
    await first.locator('summary').click();
    await page.waitForFunction(() => window.releasePlayback.length === 2);
    await first.locator('summary').click();
    await page.waitForFunction(() => !document.querySelector('details[data-comparison]').open);
    await page.evaluate(() => window.releasePlayback.forEach(resolve => resolve()));
    await page.waitForFunction(() => {
      const item = document.querySelector('details[data-comparison]');
      return !item.querySelector('[data-play-both]').disabled &&
        [...item.querySelectorAll('video')].every(video => video.paused);
    });
    console.log('PASS disclosures: default autoplay, pause on close, close during startup');
    console.log('PASS default motion: both primary videos autoplay');
  } finally {
    await browser.close();
  }
}

check().catch(error => { console.error(error); process.exitCode = 1; });
