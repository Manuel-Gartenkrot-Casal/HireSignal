// Filtro de /api/jobs a partir de req.query. Todo se fuerza a String para que
// ?source[$ne]=x (que Express parsea como objeto) no inyecte operadores de Mongo.
export function armarFiltro(query, ahora = Date.now()) {
  const [role, seniority, source, q, days, company] = ['role', 'seniority', 'source', 'q', 'days', 'company'].map(
    (k) => String(query[k] ?? ''),
  );
  const filtro = { active: true };
  if (role) filtro.role_category = role;
  if (seniority) filtro.seniority = seniority;
  if (source) filtro.sources = source;
  if (company) filtro.company = company;
  if (q) filtro.title = { $regex: q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' };
  if (Number(days) > 0) filtro.posted_date = { $gte: new Date(ahora - Number(days) * 864e5).toISOString() };
  return filtro;
}

// Señal por empresa: activas, nuevas (first_seen dentro de `days`), % senior y
// las 3 áreas con más vacantes (sin "other"). Ordena por aceleración (nuevas) y luego volumen.
export function pipelineEmpresas(days = 7, ahora = Date.now()) {
  const d = Number(days) > 0 ? Number(days) : 7;
  const desde = new Date(ahora - d * 864e5).toISOString();
  // La primera carga de una empresa (su primer día en el sistema) no cuenta como
  // nueva: si no, una empresa recién agregada parecería acelerar con todo su backlog.
  const posteriorAlAlta = { $gt: [{ $toDate: '$first_seen' }, { $add: [{ $toDate: '$alta' }, 864e5] }] };
  const nueva = { $cond: [{ $and: [{ $gte: ['$first_seen', desde] }, posteriorAlAlta] }, 1, 0] };
  return [
    { $match: { active: true } },
    { $setWindowFields: { partitionBy: '$company', output: { alta: { $min: '$first_seen' } } } },
    {
      $group: {
        _id: { c: '$company', r: '$role_category' },
        n: { $sum: 1 },
        nuevas: { $sum: nueva },
        senior: { $sum: { $cond: [{ $in: ['$seniority', ['senior', 'lead']] }, 1, 0] } },
      },
    },
    { $sort: { n: -1 } },
    {
      $group: {
        _id: '$_id.c',
        activas: { $sum: '$n' },
        nuevas: { $sum: '$nuevas' },
        senior: { $sum: '$senior' },
        areas: { $push: { area: '$_id.r', n: '$n', nuevas: '$nuevas' } },
      },
    },
    {
      $project: {
        _id: 0, empresa: '$_id', activas: 1, nuevas: 1, senior: 1,
        // "other" no le dice nada a quien vende: cuenta en activas, no como área.
        areas: { $slice: [{ $filter: { input: '$areas', cond: { $ne: ['$$this.area', 'other'] } } }, 3] },
      },
    },
    { $sort: { nuevas: -1, activas: -1 } },
  ];
}
