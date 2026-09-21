import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

import express from 'express';
import * as mongo from 'mongodb';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

let cache = globalThis.__hsMongo;

export async function conectarMongo(uri, dbName) {
  if (cache) return cache;
  const client = new mongo.MongoClient(uri, { serverSelectionTimeoutMS: 8000 });
  await client.connect();
  cache = globalThis.__hsMongo = { client, db: client.db(dbName) };
  console.log('MongoDB conectado:', uri.replace(/\/\/[^@/]+@/, '//***@'));
  return cache;
}

export default function createApp() {
  const MONGO_URI = process.env.MONGO_URI || process.env.MONGODB_URI || 'mongodb://localhost:27017/hiresignal';
  const MONGO_DB = process.env.MONGO_DB || 'hiresignal';

  const app = express();
  app.use(express.json());

  async function getDB() {
    const { db } = await conectarMongo(MONGO_URI, MONGO_DB);
    return db;
  }

  // ── GET /api/jobs ──────────────────────────────────────────────────────────
  app.get('/api/jobs', async (req, res) => {
    try {
      const { role, seniority, source, q, limit = 200 } = req.query;
      const db = await getDB();
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

  // ── GET /api/stats ─────────────────────────────────────────────────────────
  app.get('/api/stats', async (_req, res) => {
    try {
      const db = await getDB();
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

      res.json({ total, porSeniority, porRol, porFuente, recientes });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });

  // ── GET /api/health ────────────────────────────────────────────────────────
  app.get('/api/health', async (_req, res) => {
    try {
      await getDB();
      res.json({ ok: true, db: true });
    } catch (err) {
      res.status(500).json({ ok: false, db: false, error: err.message });
    }
  });

  // ── Estáticos (solo fuera de Vercel; allí los sirve la CDN) ────────────────
  if (!process.env.VERCEL) {
    const DIST_DIR = path.join(__dirname, '..', 'web', 'dist');
    const PUBLIC_DIR = fs.existsSync(DIST_DIR)
      ? DIST_DIR
      : path.join(__dirname, '..', 'web');
    app.use(express.static(PUBLIC_DIR));
    app.get(/^\/(?!api\/).*/, (_req, res) => {
      res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
    });
  }

  return app;
}