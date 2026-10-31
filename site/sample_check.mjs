import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {dirname, resolve, basename} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {evaluate, savings} from './energy.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const hash = data => createHash('sha256').update(data).digest('hex');

export async function studies(path) {
  if (path instanceof URL) path = fileURLToPath(path);
  const manifest = JSON.parse(await readFile(path, 'utf8'));
  if (manifest.schema_version !== 1) throw new Error('Unsupported sample manifest');
  const required = ['demo/patterns.gd', 'site/sample_patterns.gd', 'site/sample.py',
                    'site/energy.mjs', 'site/sample_check.mjs', 'site/electrical-inputs.json',
                    'hardware/enclosure/exports/scene.json', 'designs/stacked/exports/scene.json'];
  if (JSON.stringify(Object.keys(manifest.sources).sort()) !== JSON.stringify(required.sort()))
    throw new Error('Incomplete sample input provenance');
  for (const [name, expected] of Object.entries(manifest.sources)) {
    if (resolve(root, name).startsWith(root) && hash(await readFile(resolve(root, name))) === expected) continue;
    throw new Error(`Stale or unsafe sample input: ${name}`);
  }
  const model = JSON.parse(await readFile(new URL('./electrical-inputs.json', import.meta.url), 'utf8'));
  for (const [design, scene] of [['wide', required.find(name => name.startsWith('hardware/') && name.endsWith('scene.json'))],
                                ['narrow', required.find(name => name.startsWith('designs/') && name.endsWith('scene.json'))]]) {
    const leds = JSON.parse(await readFile(resolve(root, scene), 'utf8')).leds;
    const expected = leds.map(led => [led.group, led.index]);
    for (const set of manifest.sets.filter(row => row.design === design))
      if (JSON.stringify(set.leds.map(led => [led.group, led.index])) !== JSON.stringify(expected))
        throw new Error('Sample identities differ from native scene: ' + design);
  }
  const results = [];
  const keys = new Set();
  for (const set of manifest.sets) {
    if (!['wide', 'narrow'].includes(set.design)
        || !['rainbow', 'dark-sectors', 'dark-spirals', 'dark-diagonals'].includes(set.pattern)
        || !Number.isInteger(set.steps) || set.steps < 512 || set.steps > 8192
        || (set.steps & (set.steps - 1)) !== 0)
      throw new Error('Unsupported design, pattern or sampling interval');
    const key = `${set.design}:${set.pattern}:${set.steps}`;
    if (keys.has(key)) throw new Error(`Duplicate sample set: ${key}`);
    keys.add(key);
    if (basename(set.file) !== set.file) throw new Error('Unsafe sample filename');
    const bytes = await readFile(resolve(dirname(path), set.file));
    if (hash(bytes) !== set.sha256 || bytes.length !== set.leds.length * set.steps * 12)
      throw new Error(`Sample hash/length mismatch: ${set.file}`);
    const rgb = new Float32Array(bytes.length / 4);
    for (let i = 0; i < rgb.length; i++) rgb[i] = bytes.readFloatLE(i * 4);
    const result = evaluate({...set, rgb}, model.groups[set.design], model.defaults);
    results.push({...set, leds: undefined, result});
  }
  const convergence = [];
  let converged = true;
  for (const design of ['wide', 'narrow']) {
    for (const pattern of ['rainbow', 'dark-sectors', 'dark-spirals', 'dark-diagonals']) {
      const runs = results.filter(row => row.design === design && row.pattern === pattern).sort((a, b) => a.steps - b.steps);
      if (runs.length < 2) throw new Error(`Missing convergence pair: ${design}/${pattern}`);
      const [coarse, fine] = runs.slice(-2);
      if (fine.steps !== 2 * coarse.steps || fine.period_s !== 8 || coarse.period_s !== 8)
        throw new Error('Samples must halve the interval across the complete eight-second period');
      const delta = Math.abs(fine.result.average_battery_w - coarse.result.average_battery_w);
      const limit = Math.max(.001 * coarse.result.average_battery_w, .001);
      converged &&= delta <= limit;
      const base = results.find(row => row.design === design && row.pattern === 'rainbow' && row.steps === fine.steps);
      if (!base) throw new Error('Missing equal-settings rainbow baseline');
      convergence.push({design, pattern, steps: fine.steps, delta_w: delta, limit_w: limit,
                        ...fine.result, savings: savings(fine.result, base.result)});
    }
  }
  return {converged, status: model.status, convergence};
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    const result = await studies(process.argv[2]);
    console.log(JSON.stringify(result));
    process.exitCode = result.converged ? 0 : 2;
  } catch (error) { console.error(error.message); process.exitCode = 1; }
}
