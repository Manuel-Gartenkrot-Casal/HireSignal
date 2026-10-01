import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

import express from 'express';
import * as mongo from 'mongodb';

import { armarFiltro } from './filtro.js';

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

export const MONGO_URI = process.env.MONGO_URI || process.env.MONGODB_URI || 'mongodb://localhost:27017/hiresignal';
export const MONGO_DB = process.env.MONGO_DB || 'hiresignal';

function fallar(res, err) {
  console.error(err);
  res.status(500).json({ error: 'Error interno' });
}

export default function createApp() {

  const app = express();
  app.use(express.json());

  async function getDB() {
    const { db } = await conectarMongo(MONGO_URI, MONGO_DB);
    return db;
  }

  // ── GET /api/jobs ──────────────────────────────────────────────────────────
  app.get('/api/jobs', async (req, res) => {
    try {
      const { limit = 200 } = req.query;
      const db = await getDB();
      const filtro = armarFiltro(req.query);

      const jobs = await db.collection('jobs')
        .find(filtro, { projection: { raw: 0 } })
        .sort({ posted_date: -1 })
        .limit(Math.min(Number(limit) || 200, 1000))
        .toArray();

      res.json(jobs);
    } catch (err) {
      fallar(res, err);
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
          { $sort: { _id: -1 } },
          { $limit: 30 },
        ]).toArray(),
      ]);

      const ultimo = await col.find({ active: true }, { projection: { last_seen: 1 } }).sort({ last_seen: -1 }).limit(1).toArray();
      res.json({ total, porSeniority, porRol, porFuente, recientes: recientes.reverse(), actualizado: ultimo[0]?.last_seen ?? null });
    } catch (err) {
      fallar(res, err);
    }
  });

  // ── GET /api/health ────────────────────────────────────────────────────────
  app.get('/api/health', async (_req, res) => {
    try {
      await getDB();
      res.json({ ok: true, db: true });
    } catch (err) {
      console.error(err);
      res.status(500).json({ ok: false, db: false });
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