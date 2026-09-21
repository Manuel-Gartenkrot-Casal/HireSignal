import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

import dotenv from 'dotenv';
import express from 'express';
import * as mongo from 'mongodb';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = Number(process.env.PORT) || 3000;
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/hiresignal';
const DIST_DIR = path.join(__dirname, '..', 'web', 'dist');
const PUBLIC_DIR = fs.existsSync(DIST_DIR)
  ? DIST_DIR
  : path.join(__dirname, '..', 'web');

app.use(express.json());

let db;

async function conectarMongo() {
  const client = new mongo.MongoClient(MONGO_URI, { serverSelectionTimeoutMS: 8000 });
  await client.connect();
  db = client.db(process.env.MONGO_DB || 'hiresignal');
  console.log('MongoDB conectado:', MONGO_URI.replace(/\/\/[^@/]+@/, '//***@'));
}

// ── GET /api/jobs ────────────────────────────────────────────────────────────
app.get('/api/jobs', async (req, res) => {
  try {
    const { role, seniority, source, q, limit = 200 } = req.query;
    const filtro = { active: true };
    if (role) filtro.role_category = role;
    if (seniority && seniority !== 'unknown') filtro.seniority = seniority;
    if (source) filtro.sources = source;
    if (q) filtro.title = { $regex: String(q).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), $options: 'i' };

    const jobs = await db.collection('jobs')
      .find(filtro, { projection: { raw: 0 } })
      .sort({ posted_date: -1 })
      .limit(Math.min(Number(limit) || 200, 1000))
      .toArray();

    res.json(jobs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/stats ──────────────────────────────────────────────────────────
app.get('/api/stats', async (_req, res) => {
  try {
    const col = db.collection('jobs');
    const [total, porSeniority, porRol, porFuente, recientes] = await Promise.all([
      col.countDocuments({ active: true }),
      col.aggregate([
        { $match: { active: true } },
        { $group: { _id: '$seniority', n: { $sum: 1 } } },
        { $sort: { _id: 1 } },
      ]).toArray(),
      col.aggregate([
        { $match: { active: true } },
        { $group: { _id: '$role_category', n: { $sum: 1 } } },
        { $sort: { n: -1 } },
      ]).toArray(),
      col.aggregate([
        { $match: { active: true } },
        { $unwind: '$sources' },
        { $group: { _id: '$sources', n: { $sum: 1 } } },
        { $sort: { n: -1 } },
      ]).toArray(),
      col.aggregate([
        { $match: { active: true, posted_date: { $ne: null } } },
        { $group: { _id: { $dateToString: { format: '%Y-%m-%d', date: { $dateFromString: { dateString: '$posted_date' } } } }, n: { $sum: 1 } } },
        { $sort: { _id: 1 } },
        { $limit: 30 },
      ]).toArray(),
    ]);

    res.json({
      total,
      porSeniority,
      porRol,
      porFuente,
      recientes,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /api/health ─────────────────────────────────────────────────────────
app.get('/api/health', (_req, res) => {
  res.json({ ok: true, db: !!db });
});

// ── Estáticos (frontend build o dev) ────────────────────────────────────────
app.use(express.static(PUBLIC_DIR));
app.get(/^\/(?!api\/).*/, (_req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
});

conectarMongo()
  .then(() => {
    app.listen(PORT, () => console.log(`Dashboard corriendo en http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.error('No se pudo conectar a MongoDB:', err.message);
    process.exit(1);
  });