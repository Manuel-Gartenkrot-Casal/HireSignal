// Filtro de /api/jobs a partir de req.query. Todo se fuerza a String para que
// ?source[$ne]=x (que Express parsea como objeto) no inyecte operadores de Mongo.
export function armarFiltro(query, ahora = Date.now()) {
  const [role, seniority, source, q, days] = ['role', 'seniority', 'source', 'q', 'days'].map(
    (k) => String(query[k] ?? ''),
  );
  const filtro = { active: true };
  if (role) filtro.role_category = role;
  if (seniority) filtro.seniority = seniority;
  if (source) filtro.sources = source;
  if (q) filtro.title = { $regex: q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' };
  if (Number(days) > 0) filtro.posted_date = { $gte: new Date(ahora - Number(days) * 864e5).toISOString() };
  return filtro;
}
