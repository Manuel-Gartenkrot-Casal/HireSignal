import assert from 'node:assert/strict';
import test from 'node:test';

import { armarFiltro, pipelineEmpresas, topeJobs, validarLead } from '../src/filtro.js';

test('un objeto en la query no inyecta operadores', () => {
  const f = armarFiltro({ source: { $ne: 'x' }, role: { $gt: '' } });
  assert.equal(typeof f.sources, 'string');
  assert.equal(typeof f.role_category, 'string');
});

test('q se escapa como literal', () => {
  const f = armarFiltro({ q: 'c++ (senior)' });
  assert.equal(f.title.$regex, 'c\\+\\+ \\(senior\\)');
});

test('days filtra por fecha ISO', () => {
  const ahora = Date.parse('2026-01-10T00:00:00Z');
  assert.equal(armarFiltro({ days: '7' }, ahora).posted_date.$gte, '2026-01-03T00:00:00.000Z');
  assert.equal(armarFiltro({ days: 'abc' }, ahora).posted_date, undefined);
});

test('sin parametros solo filtra activos', () => {
  assert.deepEqual(armarFiltro({}), { active: true });
});

test('company filtra exacto y sin operadores', () => {
  assert.deepEqual(armarFiltro({ company: { $ne: 'x' } }).company, '[object Object]');
  assert.equal(armarFiltro({ company: 'Stripe' }).company, 'Stripe');
});

test('pipelineEmpresas corta nuevas por first_seen', () => {
  const ahora = Date.parse('2026-01-10T00:00:00Z');
  const corte = (p) => p[2].$group.nuevas.$sum.$cond[0].$and[0].$gte[1];
  assert.equal(corte(pipelineEmpresas('7', ahora)), '2026-01-03T00:00:00.000Z');
  assert.equal(corte(pipelineEmpresas('abc', ahora)), '2026-01-03T00:00:00.000Z');
  assert.equal(corte(pipelineEmpresas('30', ahora)), '2025-12-11T00:00:00.000Z');
});

test('validarLead acepta emails válidos y normaliza', () => {
  assert.deepEqual(validarLead({ email: ' Ana@Agencia.com ', empresa: 'Agencia' }), {
    email: 'ana@agencia.com',
    empresa: 'Agencia',
  });
  assert.equal(validarLead({ email: 'x'.repeat(250) + '@a.co' }), null);
  assert.equal(validarLead({ email: 'sin-arroba' }), null);
  assert.equal(validarLead({ email: { $ne: '' } }), null);
  assert.equal(validarLead(undefined), null);
  assert.equal(validarLead({ email: 'a@b.co', empresa: 'y'.repeat(500) }).empresa.length, 120);
});

test('topeJobs: sin clave solo muestra, con clave hasta 1000', () => {
  assert.equal(topeJobs('1000', false), 25);
  assert.equal(topeJobs(undefined, false), 25);
  assert.equal(topeJobs('5', false), 5);
  assert.equal(topeJobs('5000', true), 1000);
  assert.equal(topeJobs('abc', true), 200);
});
