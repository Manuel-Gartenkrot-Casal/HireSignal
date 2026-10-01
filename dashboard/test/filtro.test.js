import assert from 'node:assert/strict';
import test from 'node:test';

import { armarFiltro } from '../src/filtro.js';

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
