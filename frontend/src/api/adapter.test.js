import test from 'node:test';
import assert from 'node:assert/strict';
import { adaptResult } from './adapter.js';

test('backend QC and probabilities survive dashboard mapping', () => {
  const imaging = { warnings: ['negative_dixon_median_clipped_to_zero'], texture_quality: { quality: { status: 'review_required' } }, masks: { 17: { image: 'data:image/png;base64,test' } } };
  const risk = { stage: 'F0-F1', probs: [.8, .1, .05, .05], p_ge_F2: .2, tier: 'intermediate' };
  const result = adaptResult({ imaging, risk, projection: { typical: [{ years: 0, stage_value: .5 }], slower: [{ years: 0, stage_value: .5 }] }, recommendation: { headline: 'test' } }, { diabetes: 2 });
  assert.equal(result.segmentation, imaging);
  assert.equal(result.prediction, risk);
  assert.equal(result.progression.baseline[0].year, 0);
  assert.equal(result.patient.diabetes, 2);
});

import { describeTextureQuality } from './textureDisplay.js';

test('case identity comes from upload, not slice number or generic input_scan ID', () => {
  const payload = {
    imaging: { masks: {33: {}}, texture_quality: {case_id: 'input_scan'} },
    projection: {typical: [], slower: []},
  };
  const result = adaptResult(payload, {}, 'C:\\data\\chaos_patient1.zip');
  assert.equal(result.scanIdentity.label, 'chaos_patient1');
  assert.equal(result.scanIdentity.filename, 'chaos_patient1.zip');
  assert.equal(adaptResult(payload, {}).scanIdentity.label, 'Unidentified upload');
});

test('patient-level review survives an unflagged displayed slice', () => {
  const report = {
    quality: {status: 'review_required', flags: ['boundary_sensitive', 'spacing_sensitive']},
    slices: [{slice_index: 17, status: 'no_flags_detected', flags: []}],
  };
  const qc = describeTextureQuality(report);
  assert.equal(qc.label, 'Review required');
  assert.equal(qc.needsReview, true);
  assert.deepEqual(qc.flags, ['boundary sensitive', 'spacing sensitive']);
  assert.equal(describeTextureQuality(undefined).label, 'Unavailable');
  assert.equal(describeTextureQuality({quality: {status: 'invalid'}}).label, 'Not evaluable');
  assert.equal(describeTextureQuality({quality: {status: 'no_flags_detected'}}).label, 'No flags detected');
});

test('alcohol category stays separate from model risk in results', () => {
  const risk = {p_ge_F2: .02, tier: 'low'};
  const alcohol = {category: 'critical', label: 'Critical', drinks_week: 20};
  const result = adaptResult({imaging: {}, risk, alcohol_consumption: alcohol, projection: {typical: [], slower: []}}, {});
  assert.equal(result.prediction, risk);
  assert.equal(result.alcoholConsumption, alcohol);
  assert.equal(result.prediction.tier, 'low');
});

import { alcoholFromAnswers } from './alcohol.js';

test('older API without alcohol data still displays the submitted consumption', () => {
  const risk = {p_ge_F2: .07};
  const result = adaptResult({imaging: {}, risk, projection: {typical: [], slower: []}, recommendation: {disclaimer: 'Not diagnostic. LiverCast demo.'}}, {male: 0, drinks_week: 20});
  assert.equal(result.alcoholConsumption.category, 'critical');
  assert.equal(result.alcoholConsumption.drinks_week, 20);
  assert.equal(result.prediction, risk);
  assert.equal(result.recommendation.disclaimer, 'Not diagnostic. FibroLens demo.');
});

test('compatibility calculation uses exact cutoffs and rejects missing answers', () => {
  for (const [male, drinks_week, category] of [[0, 0, 'low'], [0, 7.9, 'low'], [0, 8, 'elevated'], [1, 14.9, 'low'], [1, 15, 'elevated'], [0, 20, 'critical'], [1, 20, 'critical']]) {
    assert.equal(alcoholFromAnswers({male, drinks_week}).category, category);
  }
  for (const answers of [undefined, {}, {male: 1}, {male: 1, drinks_week: NaN}, {male: true, drinks_week: 0}, {male: 1, drinks_week: -1}]) {
    assert.equal(alcoholFromAnswers(answers), null);
  }
});

import { alcoholWarning } from './alcohol.js';

test('alcohol warning is hidden for low intake and missing results', () => {
  assert.equal(alcoholWarning(alcoholFromAnswers({male: 1, drinks_week: 10})), null);
  assert.equal(alcoholWarning(alcoholFromAnswers({male: 0, drinks_week: 7})), null);
  assert.equal(alcoholWarning(null), null);
});

test('elevated and high intake produce one short warning', () => {
  for (const [male, drinks, severity] of [[0, 8, 'elevated'], [1, 15, 'elevated'], [0, 20, 'critical'], [1, 20, 'critical']]) {
    const warning = alcoholWarning(alcoholFromAnswers({male, drinks_week: drinks}));
    assert.equal(warning.severity, severity);
    assert.ok(warning.message.includes(`${drinks} drinks/week`));
    assert.ok(warning.message.length < 140);
  }
});

import { projectionAtYear, projectionOpacity } from './projectionDisplay.js';

test('projection overlay follows year and scenario and respects stage zero', () => {
  const projection = {baseline: [{year: 0, stage_value: 0}, {year: 10, stage_value: 3}], intervention: [{year: 0, stage_value: 0}, {year: 10, stage_value: 1.5}]};
  assert.equal(projectionAtYear(projection, 0, false), 0);
  assert.equal(projectionOpacity(projectionAtYear(projection, 0, false)), 0);
  assert.equal(projectionAtYear(projection, 10, false), 3);
  assert.ok(projectionOpacity(projectionAtYear(projection, 10, true)) < projectionOpacity(projectionAtYear(projection, 10, false)));
  assert.equal(projectionAtYear(projection, 11, false), null);
  assert.equal(projectionOpacity(null), 0);
  assert.equal(projectionOpacity(10), .6);
  assert.equal(projectionOpacity(-1), 0);
});
