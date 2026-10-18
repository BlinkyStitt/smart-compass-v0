const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

function comparisonPlayer(container) {
  const videos = [...container.querySelectorAll('video')];
  const playButton = container.querySelector('[data-play-both]');
  const status = container.querySelector('.play-status');
  const replayButton = container.querySelector('[data-replay-both]');
  const disclosure = container.matches('details') ? container : null;
  let linked = false;
  let attempt = null;

  function stopBoth(message = '') {
    attempt = null;
    linked = false;
    videos.forEach(video => video.pause());
    playButton.disabled = replayButton.disabled = false;
    playButton.textContent = 'Play both';
    status.textContent = message;
  }

  function checkReady() {
    const current = attempt;
    if (!current || current.requested) return;
    if (disclosure && !disclosure.open) {
      stopBoth();
      return;
    }
    if (!current.aligned) {
      if (videos.some(video => video.readyState < video.HAVE_METADATA)) return;
      current.aligned = true;
      videos.forEach(video => {
        if (video.currentTime !== current.position) video.currentTime = current.position;
      });
    }
    // Seeking can invalidate data that was ready at the previous position.
    if (!videos.every(video => !video.seeking && video.readyState >= video.HAVE_FUTURE_DATA)) return;
    current.requested = true;
    const starts = videos.map(video => {
      try { return video.play(); }
      catch (error) { return Promise.reject(error); }
    });
    // Fail immediately even if the companion play request is still pending.
    Promise.all(starts).then(() => {
      if (attempt !== current) return;
      if (disclosure && !disclosure.open) {
        stopBoth();
        return;
      }
      attempt = null;
      linked = true;
      playButton.disabled = replayButton.disabled = false;
      playButton.textContent = 'Pause both';
      status.textContent = '';
    }, () => {
      if (attempt === current) stopBoth('Playback did not start. Use Play both or open the MP4 links.');
    });
  }

  function playBoth(restart = false) {
    if (attempt || (disclosure && !disclosure.open)) return;
    const position = restart ? 0 : videos[0].currentTime;
    stopBoth();
    attempt = { position, aligned: false, requested: false };
    playButton.disabled = replayButton.disabled = true;
    playButton.textContent = 'Loading…';
    status.textContent = 'Loading both clips…';
    videos.forEach(video => {
      video.muted = true;
      video.preload = 'auto';
      // Start fetching even for the collapsed pair's preload="none" sources.
      // Keep already playable data; load() would discard it and reset the time.
      if (video.readyState < video.HAVE_FUTURE_DATA || video.error) video.load();
    });
    checkReady();
  }

  playButton.addEventListener('click', () => {
    if (linked && videos.every(video => !video.paused)) {
      stopBoth();
    } else playBoth();
  });
  replayButton.addEventListener('click', () => playBoth(true));

  videos.forEach(video => {
    video.addEventListener('pause', () => {
      // Ignore queued pause events from the beginning of a new attempt.
      if (attempt || !video.paused) return;
      linked = false;
      playButton.textContent = 'Play both';
    });
    for (const event of ['loadedmetadata', 'loadeddata', 'canplay', 'seeked']) {
      video.addEventListener(event, checkReady);
    }
    video.addEventListener('error', () => {
      stopBoth('A clip could not load. Use Play both or open its MP4 link to try it directly.');
    }, true); // Source-element errors do not bubble.
  });

  // Keep paired playback aligned after buffering, native seeking or a loop wrap.
  function sync() {
    if (linked && videos.every(video => !video.paused && video.readyState >= 3)) {
      const [first, second] = videos;
      if (Math.abs(first.currentTime - second.currentTime) > 0.10) {
        second.currentTime = first.currentTime;
      }
    }
    requestAnimationFrame(sync);
  }
  requestAnimationFrame(sync);

  if (disclosure) {
    disclosure.addEventListener('toggle', () => {
      if (disclosure.open) {
        if (!reducedMotion.matches) playBoth(true);
      } else {
        stopBoth();
      }
    });
  } else if (container.hasAttribute('data-autoplay') && !reducedMotion.matches) {
    playBoth(true);
  }
}

document.querySelectorAll('[data-comparison]').forEach(comparisonPlayer);

// Motion is opt-in when the visitor asks for reduced motion.
if (!reducedMotion.matches) document.querySelector('#assembly-video').autoplay = true;
