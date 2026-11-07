import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {evaluate, referenceCases, batteryPower, runtime, usableEnergy, savings, InputError, PowerEquilibriumError} from './energy.mjs';

export async function check() {
  const model = JSON.parse(await readFile(new URL('./electrical-inputs.json', import.meta.url), 'utf8'));
  const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-10, `${a} != ${b}`);
  const settings = {...model.defaults, path_ohm: 0};
  // Retain the historical Efest arithmetic as a regression, separate from the
  // selected cell consumed by the CLI and browser.
  near(referenceCases(model).legacy_efest.hours, 2.61664);
  near(usableEnergy(model.cell.capacity_ah, model.cell.nominal_v, 0), 21.6);
  near(referenceCases(model).selected_cell.hours, 2.9376);
  assert.equal(model.defaults.capacity_ah, model.cell.capacity_ah);
  assert.equal(model.defaults.cell_v, model.cell.nominal_v);
  assert.equal(runtime(1, 0).state, 'unbounded');
  assert.equal(runtime(1, 0).hours, null);
  assert.equal(runtime(0, 0).hours, 0);
  assert.equal(runtime(0, 1).hours, 0);
  const groups = [{id: 0, name: 'fixture', count: 1, idle_a: .001, channel_a: [.01, .02, .03]}];
  const sample = {steps: 2, period_s: 8, leds: [{group: 0, index: 0}], rgb: [1, 1, 1, 0, 0, 0]};
  const result = evaluate(sample, groups, {...settings, brightness: 1});
  near(result.average_led_a, .031); near(result.sampled_peak_led_a, .061);
  near(result.average_output_w, .155 + settings.non_led_w);
  near(result.average_battery_w, result.average_output_w / settings.efficiency + settings.quiescent_w);
  const black = evaluate(sample, groups, {...settings, brightness: 0});
  near(black.average_led_a, .001);
  assert.ok(black.runtime.hours > result.runtime.hours);
  assert.ok(savings(black, result).watts > 0);
  const zero = evaluate(sample, [{...groups[0], idle_a: 0}],
                        {...settings, brightness: 0, non_led_w: 0, quiescent_w: 0});
  assert.equal(zero.runtime.state, 'unbounded');
  assert.equal(zero.runtime.hours, null);
  near(zero.average_battery_w, 0);
  near(evaluate(sample, groups, {...settings, brightness: .5}).average_led_a, .001 + .03 * 128 / 255);
  // A saturated HSV rainbow traverses these six vertices. Two channels mix,
  // with a mean channel sum of 1.5; RGB white is not its operating load.
  const neopixel = [{id: 0, name: 'NeoPixel', count: 1, idle_a: .001, channel_a: [.02, .02, .02]}];
  const rainbow = {steps: 6, period_s: 8, leds: [{group: 0, index: 0}],
                   rgb: [1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1]};
  near(evaluate(rainbow, neopixel, {...settings, brightness: 1}).average_led_a, .031);
  near(evaluate(rainbow, neopixel, {...settings, brightness: .05}).average_led_a,
       .001 + .02 * 1.5 * 13 / 255);
  near(evaluate(rainbow, neopixel, {...settings, brightness: 0}).average_led_a, .001);
  near(evaluate(sample, groups, {...settings, reserve: 1}).runtime.hours, 0);
  near(evaluate(sample, groups, {...settings, capacity_ah: 0}).runtime.hours, 0);
  near(evaluate(sample, groups, {...settings, reserve: .5}).usable_wh, 10.8);
  near(evaluate(sample, groups, {...settings, capacity_ah: 2 * settings.capacity_ah}).runtime.hours,
       2 * evaluate(sample, groups, settings).runtime.hours);
  for (const key of Object.keys(settings)) {
    for (const invalid of [NaN, Infinity, -Infinity, -1, '1', true, null]) {
      assert.throws(() => evaluate(sample, groups, {...settings, [key]: invalid}), InputError, `${key}: ${invalid}`);
    }
  }
  for (const key of ['brightness', 'reserve', 'efficiency'])
    assert.throws(() => evaluate(sample, groups, {...settings, [key]: 1.01}), InputError);
  assert.throws(() => evaluate(sample, groups, {...settings, efficiency: 0}), InputError);
  assert.throws(() => evaluate({...sample, rgb: [1]}, groups, settings), InputError);
  assert.throws(() => evaluate({...sample, leds: [{group: 1, index: 0}]}, groups, settings), InputError);
  assert.throws(() => evaluate({...sample, rgb: [NaN, 0, 0, 0, 0, 0]}, groups, settings), InputError);
  assert.throws(() => evaluate(undefined, groups, settings), InputError);
  assert.throws(() => evaluate(sample, undefined, settings), InputError);
  assert.throws(() => evaluate(sample, groups, undefined), InputError);
  assert.throws(() => evaluate(sample, [...groups, ...groups], settings), InputError);
  assert.throws(() => evaluate({...sample, leds: [sample.leds[0], sample.leds[0]]}, groups, settings), InputError);
  const rows = evaluate({steps: 1, period_s: 8, leds: [{group: 2, index: 0}, {group: 3, index: 0}], rgb: [1, 0, 0, 0, 1, 0]},
                        [{...groups[0], id: 2}, {...groups[0], id: 3}], {...settings, brightness: 1});
  near(rows.average_led_a, .032);
  const withLoss = batteryPower(6.25, {...settings, path_ohm: .085});
  near(withLoss.watts, 6.25 / settings.efficiency + settings.quiescent_w + withLoss.amps ** 2 * .085);
  assert.throws(() => batteryPower(1000, {...settings, path_ohm: 1}), PowerEquilibriumError);
  assert.throws(() => batteryPower(1, {...settings, path_ohm: Number.MAX_VALUE}),
                error => error instanceof InputError && !(error instanceof PowerEquilibriumError));
  assert.ok(batteryPower(4, settings).watts > batteryPower(3, settings).watts);
  for (const [design, expected] of [['wide', 494], ['narrow', 466]])
    assert.equal(model.groups[design].reduce((sum, group) => sum + group.count, 0), expected);
  const {studies} = await import('./sample_check.mjs');
  const actual = await studies(new URL('../.build/energy-samples/manifest.json', import.meta.url));
  assert.ok(actual.converged, 'Actual Godot samples must converge');
  for (const row of actual.convergence) {
    if (row.pattern !== 'rainbow') {
      assert.ok(row.savings.watts > 0);
      const baseline = actual.convergence.find(base => base.design === row.design && base.pattern === 'rainbow');
      assert.ok(row.runtime.hours > baseline.runtime.hours);
    }
    assert.ok(row.sampled_peak_led_a >= row.average_led_a);
    if (row.pattern === 'rainbow') {
      const count = model.groups[row.design].reduce((sum, group) => sum + group.count, 0);
      // Check the real Godot cycle against the HSV integral, allowing only
      // independent nearest-code quantization error in each channel.
      const expected = count * (.001 + .02 * 1.5 * model.defaults.brightness);
      const rounding = count * .02 * 3 / (2 * 255);
      assert.ok(Math.abs(row.average_led_a - expected) <= rounding,
                'Shared rainbow demand must agree with its RGB duty cycle');
    }
  }
  console.log('ENERGY MODEL PASS: reference, encoding, groups, losses, reserve, zero/invalid inputs and monotonicity; hardware assumptions unqualified');
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) await check();
