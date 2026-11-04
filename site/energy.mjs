// One pure electrical calculation for CLI and browser consumers. Patterns stay
// in Godot; this module accepts time/channel samples, never screen pixels.
export class InputError extends Error {
  constructor(field, detail) { super(`${field}: ${detail}`); this.field = field; }
}

export class PowerEquilibriumError extends InputError {
  constructor() { super('path_ohm', 'load has no constant-power equilibrium; lower load or path resistance'); }
}

function number(value, field, minimum = 0, maximum = Number.MAX_VALUE) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < minimum || value > maximum)
    throw new InputError(field, `enter a finite number from ${minimum} to ${maximum}`);
  return value;
}

export function usableEnergy(capacityAh, cellV, reserve) {
  return number(capacityAh, 'capacity_ah') * number(cellV, 'cell_v', Number.MIN_VALUE)
    * (1 - number(reserve, 'reserve', 0, 1));
}

export function runtime(usableWh, batteryW) {
  number(usableWh, 'usable_wh'); number(batteryW, 'battery_w');
  if (usableWh === 0) return {hours: 0, state: 'empty', explanation: 'Zero usable energy gives zero runtime.'};
  if (batteryW === 0) return {hours: null, state: 'unbounded', explanation: 'Positive energy with zero modeled battery demand has no finite runtime.'};
  const hours = usableWh / batteryW;
  if (!Number.isFinite(hours)) throw new InputError('runtime', 'calculation exceeds the finite numeric range');
  return {hours, state: 'finite', explanation: 'Calculated hours before unmodeled losses and swap/startup downtime.'};
}

export function batteryPower(outputW, settings) {
  number(outputW, 'output_w');
  const efficiency = number(settings.efficiency, 'efficiency', Number.MIN_VALUE, 1);
  const quiescent = number(settings.quiescent_w, 'quiescent_w');
  const resistance = number(settings.path_ohm, 'path_ohm');
  const voltage = number(settings.cell_v, 'cell_v', Number.MIN_VALUE);
  const requiredW = outputW / efficiency + quiescent;
  if (!Number.isFinite(requiredW)) throw new InputError('efficiency', 'calculation exceeds the finite numeric range');
  const discriminant = voltage ** 2 - 4 * resistance * requiredW;
  if (!Number.isFinite(discriminant))
    throw new InputError('path_ohm', 'calculation exceeds the finite numeric range');
  if (discriminant < 0)
    throw new PowerEquilibriumError();
  // Rationalized high-voltage solution: avoids cancellation at R=0/small P.
  const current = 2 * requiredW / (voltage + Math.sqrt(discriminant));
  return {watts: voltage * current, amps: current, converter_v: voltage - resistance * current};
}

export function evaluate(samples, groups, settings) {
  if (!settings || typeof settings !== 'object') throw new InputError('settings', 'an electrical settings object is required');
  if (!samples || !Array.isArray(samples.leds) || !samples.rgb || typeof samples.rgb.length !== 'number')
    throw new InputError('samples', 'LED identities and RGB/time channels are required');
  if (!Array.isArray(groups) || !groups.length) throw new InputError('groups', 'group definitions are required');
  const brightness = number(settings.brightness, 'brightness', 0, 1);
  const nonLedW = number(settings.non_led_w, 'non_led_w');
  const energyWh = usableEnergy(settings.capacity_ah, settings.cell_v, settings.reserve);
  if (!Number.isFinite(energyWh)) throw new InputError('capacity_ah', 'energy exceeds the finite numeric range');
  const ids = new Set();
  const definitions = new Map();
  for (const group of groups) {
    if (!group || typeof group !== 'object') throw new InputError('groups', 'each group must be an object');
    if (!Number.isInteger(group.id) || definitions.has(group.id)) throw new InputError('groups', 'duplicate or invalid group');
    if (!Number.isInteger(group.count) || group.count <= 0) throw new InputError('groups', 'positive integer counts required');
    if (!Array.isArray(group.channel_a) || group.channel_a.length !== 3) throw new InputError('groups', 'three channel coefficients required');
    group.channel_a.forEach(value => number(value, 'channel_a'));
    number(group.idle_a, 'idle_a');
    definitions.set(group.id, {...group, found: 0});
  }
  if (!Number.isInteger(samples.steps) || samples.steps < 1) throw new InputError('steps', 'positive integer required');
  number(samples.period_s, 'period_s', Number.MIN_VALUE);
  const ledGroups = samples.leds.map(led => {
    if (!led || typeof led !== 'object') throw new InputError('leds', 'each LED needs a group/index identity');
    const key = `${led.group}:${led.index}`;
    if (!Number.isInteger(led.index) || led.index < 0 || ids.has(key)) throw new InputError('leds', 'duplicate or invalid group/index identity');
    ids.add(key);
    const group = definitions.get(led.group);
    if (!group) throw new InputError('leds', 'unknown group');
    group.found++;
    return group;
  });
  if (!ledGroups.length || [...definitions.values()].some(group => group.found !== group.count))
    throw new InputError('leds', 'scene counts differ from electrical input record');
  if (samples.rgb.length !== samples.steps * samples.leds.length * 3)
    throw new InputError('rgb', 'sample length does not match steps and LED count');
  const sums = new Map(groups.map(group => [group.id, 0]));
  let offset = 0, ledSum = 0, peak = 0, inputSum = 0, inputPeak = 0, minConverterV = Infinity;
  for (let step = 0; step < samples.steps; step++) {
    let ledA = 0;
    for (const group of ledGroups) {
      let amps = group.idle_a;
      for (let channel = 0; channel < 3; channel++) {
        const raw = number(samples.rgb[offset++], 'rgb', 0, 1);
        const pwm = Math.round(Math.min(1, Math.max(0, raw * brightness)) * 255) / 255;
        amps += pwm * group.channel_a[channel];
      }
      sums.set(group.id, sums.get(group.id) + amps);
      ledA += amps;
    }
    const input = batteryPower(5 * ledA + nonLedW, settings);
    ledSum += ledA; peak = Math.max(peak, ledA);
    inputSum += input.watts; inputPeak = Math.max(inputPeak, input.watts);
    minConverterV = Math.min(minConverterV, input.converter_v);
  }
  const batteryW = inputSum / samples.steps;
  return {
    average_led_a: ledSum / samples.steps, sampled_peak_led_a: peak,
    groups: groups.map(group => ({id: group.id, name: group.name, count: group.count, average_a: sums.get(group.id) / samples.steps})),
    average_output_w: 5 * ledSum / samples.steps + nonLedW, non_led_w: nonLedW,
    average_battery_w: batteryW, sampled_peak_battery_w: inputPeak,
    average_battery_a: batteryW / settings.cell_v, cell_v: settings.cell_v,
    sampled_min_converter_v: minConverterV, usable_wh: energyWh,
    runtime: runtime(energyWh, batteryW), sample_steps: samples.steps,
    sample_interval_s: samples.period_s / samples.steps, sample_period_s: samples.period_s,
    peak_basis: 'Sampled encoded channel demand; excludes unsampled PWM/radio/inrush/fault peaks.',
  };
}

export function savings(result, baseline) {
  const watts = baseline.average_battery_w - result.average_battery_w;
  return {watts, percent: baseline.average_battery_w === 0 ? 0 : 100 * watts / baseline.average_battery_w};
}

async function main() {
  const {readFile} = await import('node:fs/promises');
  if (process.argv[2] === '--check') {
    // A separate entry point avoids awaiting a module that imports this module
    // while this module's own top-level CLI await is still pending.
    const {spawnSync} = await import('node:child_process');
    const {fileURLToPath} = await import('node:url');
    const result = spawnSync(process.execPath, [fileURLToPath(new URL('./test_energy.mjs', import.meta.url))], {stdio: 'inherit'});
    if (result.error) throw result.error;
    if (result.status !== 0) throw new Error(`Energy checks failed: ${result.status ?? result.signal}`);
  } else if (process.argv[2] === '--reference') {
    const model = JSON.parse(await readFile(new URL('./electrical-inputs.json', import.meta.url), 'utf8'));
    const wh = usableEnergy(model.cell.capacity_ah, model.cell.nominal_v, 0);
    console.log(JSON.stringify(runtime(wh, model.reference.output_w / model.reference.efficiency)));
  } else if (process.argv[2] === '--evaluate') {
    let input = '';
    for await (const chunk of process.stdin) input += chunk;
    const data = JSON.parse(input);
    console.log(JSON.stringify(evaluate(data.samples, data.groups, data.settings)));
  } else {
    throw new Error('Usage: node site/energy.mjs --check | --reference | --evaluate < inputs.json');
  }
}

if (typeof process !== 'undefined' && process.argv[1]) {
  const {pathToFileURL} = await import('node:url');
  if (pathToFileURL(process.argv[1]).href === import.meta.url) {
    try { await main(); } catch (error) { console.error(error.message); process.exitCode = 1; }
  }
}
