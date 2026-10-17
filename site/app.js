const videos = [...document.querySelectorAll('.film video')];
const playButton = document.querySelector('#play-both');
const status = document.querySelector('#play-status');
const replayButton = document.querySelector('#replay-both');
let linked = false;
let starting = false;

async function playBoth(restart = false) {
  if (starting) return;
  starting = true;
  playButton.disabled = replayButton.disabled = true;
  playButton.textContent = 'Loading…';
  status.textContent = 'Loading both clips…';
  linked = false;
  videos.forEach(video => {
    video.muted = true;
    if (restart) video.currentTime = 0;
    else if (video !== videos[0]) video.currentTime = videos[0].currentTime;
  });
  const results = await Promise.allSettled(videos.map(video => video.play()));
  starting = false;
  playButton.disabled = replayButton.disabled = false;
  linked = results.every(result => result.status === 'fulfilled');
  if (!linked) videos.forEach(video => video.pause());
  playButton.textContent = linked ? 'Pause both' : 'Play both';
  status.textContent = linked ? '' : 'Playback did not start. Use Play both or open the MP4 links.';
}

playButton.addEventListener('click', () => {
  if (linked && videos.every(video => !video.paused)) {
    linked = false;
    videos.forEach(video => video.pause());
    playButton.textContent = 'Play both';
  } else playBoth();
});
replayButton.addEventListener('click', () => playBoth(true));

videos.forEach(video => {
  video.addEventListener('pause', () => {
    if (starting) return;
    linked = false;
    playButton.textContent = 'Play both';
  });
  video.addEventListener('error', () => {
    status.textContent = 'A clip could not load. Open its MP4 link to try it directly.';
  });
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

// Motion is opt-in when the visitor asks for reduced motion.
if (!matchMedia('(prefers-reduced-motion: reduce)').matches) playBoth(true);
