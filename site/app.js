const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const players = new Map();
let viewerOpen = false;

function autoplayAllowed(container) {
  return container?.hasAttribute('data-assembly') || !reducedMotion.matches;
}

function player(container) {
  const video = container.querySelector('video');
  const playButton = container.querySelector('[data-play]');
  const restartButton = container.querySelector('[data-replay]');
  const status = container.querySelector('.play-status');
  const disclosure = container.matches('details') ? container : null;
  let attempt = null;
  let wanted = container.hasAttribute('data-autoplay') && autoplayAllowed(container);
  let visible = false;

  function eligible() {
    return wanted && visible && !document.hidden && !viewerOpen && (!disclosure || disclosure.open);
  }

  function stop(message = '') {
    attempt = null;
    video.pause();
    playButton.textContent = 'Play';
    playButton.disabled = restartButton.disabled = false;
    status.textContent = message;
  }

  function sync() {
    if (!eligible()) { stop(); return; }
    if (attempt || !video.paused) return;
    const current = {};
    attempt = current;
    video.muted = true;
    video.preload = 'auto';
    playButton.textContent = 'Loading…';
    playButton.disabled = restartButton.disabled = true;
    status.textContent = 'Loading clip…';
    if (video.error) video.load();
    Promise.resolve().then(() => {
      if (attempt === current && eligible()) return video.play();
    }).then(() => {
      if (attempt !== current) return;
      attempt = null;
      if (!eligible()) { stop(); return; }
      playButton.disabled = restartButton.disabled = false;
      playButton.textContent = 'Pause';
      status.textContent = '';
    }, () => {
      if (attempt === current) {
        wanted = false;
        stop('Playback did not start. Use Play or open the MP4 link.');
      }
    });
  }

  playButton.addEventListener('click', () => { wanted = !wanted; sync(); });
  restartButton.addEventListener('click', () => {
    stop();
    video.currentTime = 0;
    wanted = true;
    sync();
  });
  video.addEventListener('pause', () => { if (!attempt && video.paused) playButton.textContent = 'Play'; });
  video.addEventListener('play', () => {
    if (!eligible()) stop();
    else if (!attempt) playButton.textContent = 'Pause';
  });
  video.addEventListener('error', () => {
    wanted = false;
    stop('The clip could not load. Use Play or open its MP4 link.');
  }, true);
  reducedMotion.addEventListener('change', () => {
    if (!autoplayAllowed(container)) { wanted = false; sync(); }
  });
  if (disclosure) disclosure.addEventListener('toggle', () => {
    wanted = disclosure.open && !reducedMotion.matches;
    sync();
  });
  const observer = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    sync();
  });
  observer.observe(video);
  players.set(video, {sync});
}

document.querySelectorAll('[data-player]').forEach(player);
document.addEventListener('visibilitychange', () => {
  players.forEach(controller => controller.sync());
  if (document.hidden && activeMedia instanceof HTMLVideoElement) activeMedia.pause();
});

// A modal fills the viewport on every client. The Fullscreen API also hides
// browser chrome where supported. Direct image and MP4 links work without JS.
const viewer = document.createElement('dialog');
viewer.className = 'media-viewer';
viewer.setAttribute('aria-label', 'Full-screen media');
const closeButton = document.createElement('button');
closeButton.className = 'media-close';
closeButton.type = 'button';
closeButton.textContent = 'Close ×';
const caption = document.createElement('p');
const message = document.createElement('p');
message.setAttribute('role', 'status');
viewer.append(closeButton, caption, message);
document.body.append(viewer);
let activeMedia = null;
let opener = null;
let nativeFullscreen = false;

function closeViewer() {
  if (document.fullscreenElement === viewer) document.exitFullscreen().catch(() => {});
  viewer.close();
}
closeButton.addEventListener('click', closeViewer);
viewer.addEventListener('click', event => { if (event.target === viewer) closeViewer(); });
viewer.addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  const controls = activeMedia instanceof HTMLVideoElement ? [closeButton, activeMedia] : [closeButton];
  const current = controls.indexOf(document.activeElement);
  const next = (current + (event.shiftKey ? -1 : 1) + controls.length) % controls.length;
  event.preventDefault();
  controls[next].focus();
});
viewer.addEventListener('close', () => {
  if (activeMedia instanceof HTMLVideoElement) {
    activeMedia.pause();
    activeMedia.removeAttribute('src');
    activeMedia.load();
  }
  activeMedia?.remove();
  activeMedia = null;
  nativeFullscreen = false;
  viewerOpen = false;
  players.forEach(controller => controller.sync());
  opener?.focus({preventScroll: true});
});
document.addEventListener('fullscreenchange', () => {
  if (document.fullscreenElement === viewer) nativeFullscreen = true;
  else if (nativeFullscreen && viewer.open) viewer.close();
});

function openViewer(trigger, original, src) {
  opener = trigger;
  viewerOpen = true;
  players.forEach(controller => controller.sync());
  message.textContent = '';
  const isVideo = original instanceof HTMLVideoElement;
  const media = document.createElement(isVideo ? 'video' : 'img');
  const label = original.getAttribute('alt') || original.getAttribute('aria-label') || 'Prototype view';
  caption.textContent = label;
  if (isVideo) {
    media.autoplay = original.autoplay;
    media.controls = true;
    media.tabIndex = 0;
    media.loop = true;
    media.muted = true;
    media.playsInline = true;
    media.addEventListener('loadedmetadata', () => { media.currentTime = original.currentTime; }, {once: true});
  } else {
    media.alt = label;
  }
  media.addEventListener('error', () => { message.textContent = 'This view could not load. Close it and use the direct file link to retry.'; });
  media.src = src;
  activeMedia = media;
  viewer.insertBefore(media, caption);
  viewer.showModal();
  closeButton.focus();
  if (viewer.requestFullscreen) viewer.requestFullscreen().catch(() => {});
  if (isVideo && autoplayAllowed(original.closest('[data-player]'))) media.play().catch(() => {});
}

document.querySelectorAll('a:has(img)').forEach(link => {
  const image = link.querySelector('img');
  link.setAttribute('aria-haspopup', 'dialog');
  link.addEventListener('click', event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    openViewer(link, image, image.currentSrc || link.href);
  });
});
document.querySelectorAll('video').forEach(video => {
  video.classList.add('media-expand');
  video.tabIndex = 0;
  video.setAttribute('role', 'button');
  video.setAttribute('aria-description', 'Open full screen');
  video.setAttribute('aria-haspopup', 'dialog');
  const open = () => openViewer(video, video, video.currentSrc || video.src);
  video.addEventListener('click', open);
  video.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open();
  });
});
