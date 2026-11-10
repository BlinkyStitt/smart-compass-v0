import {evaluate, savings, usableEnergy, InputError, PowerEquilibriumError} from './energy.mjs';

const fields = [
  ['brightness', 'Brightness (%)', 0, 100, .1],
  ['capacity_ah', 'Cell capacity (Ah)', 0, '', .1],
  ['energy_wh', 'Usable cell energy (Wh, after reserve)', 0, '', .01],
  ['efficiency', 'Conversion efficiency (%)', .01, 100, .1],
  ['reserve', 'Reserve and cutoff allowance (%)', 0, 100, .1],
  ['non_led_w', 'Controller, sensors and radio output (W)', 0, '', .01],
  ['quiescent_w', 'Converter and protection input (W)', 0, '', .001],
  ['path_ohm', 'Contact and wiring resistance (Ω)', 0, '', .001],
];
const patterns = ['rainbow', 'dark-sectors', 'dark-spirals', 'dark-diagonals'];
const names = ['Full rainbow', 'Rainbow • dark sectors', 'Rainbow • dark spirals', 'Rainbow • dark diagonals'];
const display = value => Number(value.toPrecision(12)).toString();

export async function loadSample(set) {
  const response = await fetch('pattern-data/' + set.file);
  if (!response.ok) throw new InputError('samples', 'pattern data could not load; try Reset');
  const bytes = await response.arrayBuffer();
  const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
    .map(value => value.toString(16).padStart(2, '0')).join('');
  if (hash !== set.sha256 || bytes.byteLength !== set.steps * set.leds.length * 12)
    throw new InputError('samples', 'pattern data is stale or damaged; reload the page');
  const view = new DataView(bytes), rgb = new Float32Array(bytes.byteLength / 4);
  for (let i = 0; i < rgb.length; i++) rgb[i] = view.getFloat32(i * 4, true);
  return {...set, rgb};
}

export function mountCalculator(root, model, manifest, loader = loadSample) {
  const fieldMarkup = ([id, label, min, max, step]) => `<label for="energy-${id}">${label}<input id="energy-${id}" name="${id}" type="number" min="${min}" ${max === '' ? '' : `max="${max}"`} step="${step}" required aria-describedby="energy-error"></label>`;
  root.innerHTML = `<h2>Battery life</h2>
    <p>Estimate how long one battery will last. Actual runtime has not been measured.</p>
    <form id="energy-form" novalidate>
      <input name="design" type="hidden" value="narrow">
      <div class="energy-fields">
        <div><label for="energy-pattern">Pattern</label><select id="energy-pattern" name="pattern">${patterns.map((pattern, i) => `<option value="${pattern}">${names[i]}</option>`).join('')}</select></div>
        ${fieldMarkup(fields[0])}
      </div>
      <details id="energy-advanced"><summary>Advanced settings</summary>
        <p id="energy-basis"></p>
        <p>These settings estimate battery life; they do not set safe operating limits.</p>
        <div class="energy-fields">${fields.slice(1).map(fieldMarkup).join('')}</div>
      </details>
      <button type="reset">Reset calculator</button>
    </form>
    <p id="energy-error" role="alert"></p>
    <div id="energy-result" role="status" aria-live="polite" aria-atomic="true"></div>
    <p id="energy-video-note">Calculator settings do not change the video above.</p>`;
  const form = root.querySelector('form');
  const result = root.querySelector('#energy-result');
  const error = root.querySelector('#energy-error');
  const inputs = Object.fromEntries([...form.elements].filter(element => element.name).map(element => [element.name, element]));
  root.querySelector('#energy-basis').textContent = `Battery: ${model.cell.name}.`;
  let generation = 0;
  const cache = new Map();
  const numeric = key => {
    const field = inputs[key], value = field.valueAsNumber;
    if (!Number.isFinite(value) || field.value.trim() === '' || value < Number(field.min)
        || (field.max !== '' && value > Number(field.max)))
      throw new InputError(key, `enter a finite value of at least ${field.min}${field.max ? ' and at most ' + field.max : ''}`);
    return value;
  };
  function settings(changed) {
    const reserve = numeric('reserve') / 100;
    if (changed === 'energy_wh') {
      const wh = numeric('energy_wh');
      if (reserve === 1 && wh > 0) throw new InputError('reserve', 'reduce reserve below 100% before entering positive usable energy');
      inputs.capacity_ah.value = display(reserve === 1 ? 0 : wh / (model.cell.nominal_v * (1 - reserve)));
    }
    const capacity = numeric('capacity_ah');
    inputs.energy_wh.value = display(usableEnergy(capacity, model.cell.nominal_v, reserve));
    return {cell_v: model.cell.nominal_v, capacity_ah: capacity, reserve,
            brightness: numeric('brightness') / 100, efficiency: numeric('efficiency') / 100,
            non_led_w: numeric('non_led_w'), quiescent_w: numeric('quiescent_w'), path_ohm: numeric('path_ohm')};
  }
  async function sample(design, pattern) {
    const candidates = manifest.sets.filter(set => set.design === design && set.pattern === pattern).sort((a, b) => b.steps - a.steps);
    if (!candidates.length) throw new InputError('samples', 'this design/pattern has no verified samples');
    const set = candidates[0], key = `${design}/${pattern}/${set.sha256}`;
    if (!cache.has(key)) cache.set(key, loader(set).catch(reason => { cache.delete(key); throw reason; }));
    return cache.get(key);
  }
  async function update(changed) {
    const current = ++generation;
    result.textContent = ''; result.hidden = true; delete result.dataset.result;
    error.textContent = ''; root.setAttribute('aria-busy', 'true');
    Object.values(inputs).forEach(field => field.removeAttribute('aria-invalid'));
    try {
      const values = settings(changed), design = inputs.design.value, pattern = inputs.pattern.value;
      const [selected, base] = await Promise.all([sample(design, pattern), sample(design, 'rainbow')]);
      if (current !== generation) return;
      const value = evaluate(selected, model.groups[design], values);
      let saved;
      try {
        const baseline = evaluate(base, model.groups[design], values);
        saved = {state: 'available', ...savings(value, baseline)};
      } catch (reason) {
        if (!(reason instanceof PowerEquilibriumError)) throw reason;
        saved = {state: 'unavailable', watts: null, percent: null,
                 explanation: 'Full-rainbow comparison unavailable: its load has no constant-power equilibrium at these settings.'};
      }
      result.dataset.result = JSON.stringify({design, pattern, settings: values, ...value, savings: saved});
      const duration = document.createElement('strong');
      if (value.runtime.state === 'unbounded') {
        duration.textContent = 'No finite runtime at zero power demand.';
      } else if (value.runtime.hours >= 1e6) {
        duration.textContent = `About ${value.runtime.hours.toPrecision(3)} h per battery`;
      } else {
        const minutes = Math.round(value.runtime.hours * 60);
        const hours = Math.floor(minutes / 60), remainder = minutes % 60;
        const time = hours ? `${hours} h${remainder ? ` ${remainder} min` : ''}` : `${remainder} min`;
        duration.textContent = `About ${time} per battery`;
      }
      const context = document.createElement('p');
      context.textContent = `${names[patterns.indexOf(pattern)]} at ${display(values.brightness * 100)}% brightness.`;
      result.replaceChildren(duration, context);
      if (pattern !== 'rainbow' && (saved.state === 'unavailable' || saved.percent >= .5)) {
        const comparison = document.createElement('p');
        comparison.textContent = saved.state === 'available'
          ? `Uses about ${saved.percent.toFixed(0)}% less power than full rainbow at the same brightness.`
          : 'Full-rainbow comparison unavailable at these settings.';
        result.append(comparison);
      }
      result.hidden = false;
    } catch (reason) {
      if (current !== generation) return;
      const field = inputs[reason.field];
      if (field) {
        field.setAttribute('aria-invalid', 'true');
        const advanced = field.closest('details');
        if (advanced) advanced.open = true;
      }
      error.textContent = reason.message || 'Calculation failed; check inputs and try Reset.';
    } finally {
      if (current === generation) root.setAttribute('aria-busy', 'false');
    }
  }
  function reset() {
    inputs.design.value = 'narrow'; inputs.pattern.value = 'rainbow';
    for (const [key, value] of Object.entries(model.defaults)) {
      if (inputs[key]) inputs[key].value = display(['brightness', 'efficiency', 'reserve'].includes(key) ? value * 100 : value);
    }
    return update();
  }
  form.addEventListener('input', event => { void update(event.target.name); });
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('reset', event => { event.preventDefault(); void reset(); });
  return {ready: reset()};
}

const root = typeof document === 'undefined' ? null : document.querySelector('#energy-calculator');
if (root) {
  try {
    const responses = await Promise.all(['electrical-inputs.json', 'pattern-samples.json'].map(path => fetch(path)));
    if (responses.some(response => !response.ok)) throw new Error('Calculator data could not load; reload this page.');
    const [model, manifest] = await Promise.all(responses.map(response => response.json()));
    mountCalculator(root, model, manifest);
  } catch (error) { root.textContent = error.message; root.setAttribute('role', 'alert'); }
}
