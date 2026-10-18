// Run against the built site with Playwright and Chromium installed.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

async function playbackPage(browser, reducedMotion = 'no-preference') {
  const page = await browser.newPage({ reducedMotion });
  // Observe real play requests, with optional deferred completions for race tests.
  await page.addInitScript(() => {
    const play = HTMLMediaElement.prototype.play;
    window.playCalls = [];
    window.pendingStarts = [];
    window.holdStarts = false;
    HTMLMediaElement.prototype.play = function () {
      if (!this.closest('[data-comparison]')) return play.call(this);
      window.playCalls.push({
        id: this.id,
        pair: [...this.closest('[data-comparison]').querySelectorAll('video')]
          .map(video => ({ ready: video.readyState, seeking: video.seeking, time: video.currentTime })),
      });
      if (window.throwStart === this.id) throw new Error('Controlled synchronous rejection');
      const result = play.call(this);
      if (!window.holdStarts) return result;
      return result.then(() => new Promise((resolve, reject) => {
        window.pendingStarts.push({ id: this.id, resolve, reject });
      }));
    };
  });
  return page;
}

async function waitPlaying(page, selector = '#films') {
  await page.waitForFunction(selector => {
    const pair = document.querySelector(selector);
    const videos = [...pair.querySelectorAll('video')];
    return pair.querySelector('[data-play-both]').textContent === 'Pause both'
      && pair.querySelector('.play-status').textContent === ''
      && videos.every(video => !video.paused && video.currentTime > 0.1)
      && Math.abs(videos[0].currentTime - videos[1].currentTime) <= 0.10;
  }, selector);
}

async function assertStopped(page, selector = '#films', message = '') {
  await page.waitForFunction(({ selector, message }) => {
    const pair = document.querySelector(selector);
    return [...pair.querySelectorAll('video')].every(video => video.paused)
      && pair.querySelector('[data-play-both]').textContent === 'Play both'
      && pair.querySelector('.play-status').textContent === message;
  }, { selector, message });
  const state = await page.locator(selector).evaluate(pair => ({
    paused: [...pair.querySelectorAll('video')].every(video => video.paused),
    disabled: [...pair.querySelectorAll('button')].some(button => button.disabled),
    button: pair.querySelector('[data-play-both]').textContent,
    status: pair.querySelector('.play-status').textContent,
  }));
  assert.deepEqual(state, { paused: true, disabled: false, button: 'Play both', status: message });
}

async function holdMedia(page, source) {
  let release;
  let requested;
  const gate = new Promise(resolve => { release = resolve; });
  const seen = new Promise(resolve => { requested = resolve; });
  await page.route(source, async route => {
    requested();
    await gate;
    await route.continue();
  });
  return { release, seen };
}

async function checkPlayback(browser, url, sources) {
  const silverPair = 'details[data-comparison]:has(#silver-wide-video)';
  for (const slow of ['wide-video', 'narrow-video']) {
    const page = await playbackPage(browser);
    const held = await holdMedia(page, sources[slow]);
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await held.seen;
    const fast = slow === 'wide-video' ? 'narrow-video' : 'wide-video';
    await page.waitForFunction(id => document.getElementById(id).readyState >= 3, fast);
    await page.waitForTimeout(200);
    assert.ok(await page.locator('#films video').evaluateAll(videos =>
      videos.every(video => video.paused && video.currentTime === 0)), 'neither clip starts early');
    assert.equal(await page.evaluate(() => window.playCalls.length), 0);
    assert.equal(await page.locator('#play-status').textContent(), 'Loading both clips…');
    held.release();
    await waitPlaying(page);
    const calls = await page.evaluate(() => window.playCalls);
    assert.deepEqual(calls.map(call => call.id).sort(), ['narrow-video', 'wide-video']);
    assert.ok(calls.every(call => call.pair.every(video =>
      video.ready >= 3 && !video.seeking && video.time < 0.1)), 'both requests see ready, aligned media');
    await page.locator('#films video').evaluateAll(videos => videos.forEach(video => {
      for (const event of ['loadedmetadata', 'canplay', 'seeked']) video.dispatchEvent(new Event(event));
    }));
    assert.equal(await page.evaluate(() => window.playCalls.length), 2, 'readiness events cannot duplicate starts');
    console.log(`PASS delayed ${slow}: readiness gate, concurrent starts and 100 ms sync`);
    await page.close();
  }

  const cached = await playbackPage(browser, 'reduce');
  await cached.goto(url);
  // Python's simple server has no Range support. Cache the real clips as blobs
  // so nonzero seeking in this fixture does not depend on server capabilities.
  await cached.locator('#films video').evaluateAll(videos => Promise.all(videos.map(async video => {
    const response = await fetch(video.querySelector('source').src);
    video.src = URL.createObjectURL(await response.blob());
    video.preload = 'auto';
    video.load();
  })));
  await cached.waitForFunction(() => [...document.querySelectorAll('#films video')]
    .every(video => video.readyState >= 3 && video.seekable.length && video.seekable.end(0) > 8));
  await cached.locator('#films video').evaluateAll(videos => {
    videos[0].currentTime = 4;
    videos[1].currentTime = 8;
  });
  await cached.waitForFunction(() => [...document.querySelectorAll('#films video')]
    .every(video => video.readyState >= 3 && !video.seeking));
  await cached.evaluate(() => {
    const video = document.querySelector('#narrow-video');
    const time = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, 'currentTime');
    // Hold readiness AFTER alignment, even though both clips were initially cached.
    Object.defineProperty(video, 'currentTime', {
      configurable: true,
      get() { return time.get.call(this); },
      set(value) {
        time.set.call(this, value);
        Object.defineProperty(this, 'readyState', { configurable: true, value: 2 });
        Object.defineProperty(this, 'seeking', { configurable: true, value: true });
      },
    });
    window.reloads = 0;
    document.querySelectorAll('#films video').forEach(video =>
      video.addEventListener('loadstart', () => window.reloads++));
  });
  await cached.locator('#play-both').click();
  assert.equal(await cached.evaluate(() => window.playCalls.length), 0, 'wait for data at the aligned position');
  await cached.evaluate(() => {
    const video = document.querySelector('#narrow-video');
    Object.defineProperty(video, 'readyState', { configurable: true, value: 4 });
    video.dispatchEvent(new Event('canplay'));
  });
  assert.equal(await cached.evaluate(() => window.playCalls.length), 0, 'wait for alignment seek to finish');
  await cached.evaluate(() => {
    const video = document.querySelector('#narrow-video');
    delete video.currentTime;
    delete video.readyState;
    delete video.seeking;
    video.dispatchEvent(new Event('seeked'));
  });
  await waitPlaying(cached);
  assert.ok((await cached.evaluate(() => window.playCalls))
    .every(call => call.pair.every(video => video.time >= 4 && video.time < 4.1)), 'resume at the first clip’s time');
  assert.equal(await cached.evaluate(() => window.reloads), 0, 'cached readiness must not require new load events');
  await cached.locator('#play-both').click();
  await assertStopped(cached);
  await cached.locator('#replay-both').click();
  await waitPlaying(cached);
  assert.ok((await cached.evaluate(() => window.playCalls.slice(-2)))
    .every(call => call.pair.every(video => video.time < 0.1)), 'restart aligns at zero');
  // Force drift on seekable media, then watch a real loop wrap.
  assert.ok(await cached.locator('#films video').evaluateAll(videos => {
    videos[0].currentTime = videos[0].duration - 0.3;
    videos[1].currentTime = 3;
    return videos[0].currentTime > 15 && videos[1].currentTime >= 3;
  }), 'fixture must seek to opposite sides of the loop');
  await cached.waitForFunction(() => document.querySelector('#wide-video').currentTime < 1);
  await waitPlaying(cached);
  await cached.locator('#films video').evaluateAll(videos => {
    Object.defineProperty(videos[1], 'readyState', { configurable: true, value: 2 });
    videos[0].currentTime = 5;
    videos[1].currentTime = 2;
  });
  await cached.waitForTimeout(200);
  assert.ok(await cached.locator('#narrow-video').evaluate(video => video.currentTime < 3),
    'drift correction waits for buffered data');
  await cached.locator('#narrow-video').evaluate(video => { delete video.readyState; });
  await waitPlaying(cached);
  await cached.locator(`${silverPair} summary`).click();
  await assertStopped(cached, silverPair);
  await cached.locator(`${silverPair} [data-play-both]`).click();
  await waitPlaying(cached, silverPair);
  await cached.locator(`${silverPair} summary`).click();
  await assertStopped(cached, silverPair);
  await waitPlaying(cached);
  console.log('PASS cached readiness, post-alignment seek, resume/restart, loop/buffering sync, reduced-motion silver and pair independence');
  await cached.close();

  const silver = await playbackPage(browser);
  const held = await holdMedia(silver, sources['silver-narrow-video']);
  await silver.goto(url);
  await waitPlaying(silver);
  await silver.locator(`${silverPair} summary`).click();
  await held.seen;
  assert.equal(await silver.locator(`${silverPair} .play-status`).textContent(), 'Loading both clips…');
  await silver.locator(`${silverPair} summary`).click();
  await assertStopped(silver, silverPair);
  held.release();
  await silver.waitForFunction(() => document.querySelector('#silver-narrow-video').readyState >= 3);
  await assertStopped(silver, silverPair);
  await silver.evaluate(() => { window.holdStarts = true; });
  await silver.locator(`${silverPair} summary`).click();
  await silver.waitForFunction(() => window.pendingStarts.length === 2);
  await silver.locator(`${silverPair} summary`).click();
  await assertStopped(silver, silverPair);
  await silver.locator(`${silverPair} summary`).click();
  await silver.waitForFunction(() => window.pendingStarts.length === 4);
  await silver.evaluate(() => {
    window.pendingStarts[0].resolve();
    window.pendingStarts[1].reject(new Error('Stale attempt'));
  });
  assert.equal(await silver.locator(`${silverPair} .play-status`).textContent(), 'Loading both clips…');
  await silver.evaluate(() => window.pendingStarts[2].resolve());
  assert.equal(await silver.locator(`${silverPair} .play-status`).textContent(), 'Loading both clips…',
    'one successful request must not clear loading');
  await silver.evaluate(() => window.pendingStarts[3].resolve());
  await waitPlaying(silver, silverPair);
  await waitPlaying(silver);
  await silver.locator(`${silverPair} summary`).click();
  await silver.evaluate(() => document.querySelector('#silver-wide-video').dispatchEvent(new Event('canplay')));
  await assertStopped(silver, silverPair);
  console.log('PASS silver close during loading, late readiness, reopen and stale play completions');
  await silver.close();

  // A rejected start or media error must fail before its companion settles.
  for (const failure of ['rejection', 'media-error', 'source-error', 'synchronous-rejection']) {
    const page = await playbackPage(browser, 'reduce');
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    await page.waitForFunction(() => [...document.querySelectorAll('#films video')]
      .every(video => video.readyState >= 3));
    await page.evaluate(failure => {
      window.holdStarts = true;
      if (failure === 'synchronous-rejection') window.throwStart = 'narrow-video';
    }, failure);
    await page.locator('#play-both').click();
    if (failure !== 'synchronous-rejection') {
      await page.waitForFunction(() => window.pendingStarts.length === 2);
      assert.equal(await page.locator('#play-status').textContent(), 'Loading both clips…');
      // Repeated interactions and events must not issue another start.
      await page.evaluate(() => {
        document.querySelector('#replay-both').dispatchEvent(new Event('click'));
        document.querySelector('#wide-video').dispatchEvent(new Event('canplay'));
      });
      assert.equal(await page.evaluate(() => window.playCalls.length), 2);
      await page.evaluate(failure => {
        if (failure === 'rejection') window.pendingStarts[1].reject(new Error('Controlled rejection'));
        else document.querySelector(failure === 'source-error' ? '#wide-video source' : '#wide-video')
          .dispatchEvent(new Event('error'));
      }, failure);
    }
    const message = failure.endsWith('error')
      ? 'A clip could not load. Use Play both or open its MP4 link to try it directly.'
      : 'Playback did not start. Use Play both or open the MP4 links.';
    await page.waitForFunction(message => document.querySelector('#play-status').textContent === message, message);
    await assertStopped(page, '#films', message);
    await page.evaluate(() => { window.holdStarts = false; window.throwStart = null; });
    await page.locator('#play-both').click();
    await waitPlaying(page);
    await page.evaluate(() => window.pendingStarts.forEach(start => start.resolve()));
    await waitPlaying(page);
    assert.deepEqual(errors, [], 'stale failures must be handled without unhandled rejections');
    console.log(`PASS ${failure}: prompt paired stop, restored controls, retry and stale completion`);
    await page.close();
  }

  const failedLoad = await playbackPage(browser);
  const blocked = await holdMedia(failedLoad, sources['narrow-video']);
  await failedLoad.route(sources['wide-video'], route => route.abort('failed'));
  await failedLoad.goto(url, { waitUntil: 'domcontentloaded' });
  await blocked.seen;
  await failedLoad.waitForFunction(() => document.querySelector('#play-status').textContent.includes('could not load'));
  await assertStopped(failedLoad, '#films', 'A clip could not load. Use Play both or open its MP4 link to try it directly.');
  blocked.release();
  await failedLoad.waitForFunction(() => document.querySelector('#narrow-video').readyState >= 3);
  assert.equal(await failedLoad.evaluate(() => window.playCalls.length), 0);
  console.log('PASS network failure while companion loads: no late startup');
  await failedLoad.close();
}

async function check() {
  const browser = await chromium.launch({ headless: true });
  const url = process.argv[2] || 'http://127.0.0.1:8080';
  const names = ['Rainbow • dark sectors', 'Rainbow • dark spirals',
    'Rainbow • dark diagonals', 'Silver PETG rings'];
  try {
    let sources;
    for (const width of [320, 375, 620, 621, 1440, 1600, 1920]) {
      const page = await browser.newPage({
        viewport: { width, height: 900 }, reducedMotion: 'reduce',
      });
      await page.goto(url);
      sources = await page.locator('[data-comparison] video').evaluateAll(videos =>
        Object.fromEntries(videos.map(video => [video.id, video.querySelector('source').src])));
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
    await page.close();
    await checkPlayback(browser, url, sources);
  } finally {
    await browser.close();
  }
}

check().catch(error => { console.error(error); process.exitCode = 1; });
