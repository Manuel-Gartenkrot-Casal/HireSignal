import 'dotenv/config';

import createApp, { conectarMongo } from './app.js';

const PORT = Number(process.env.PORT) || 3000;
const MONGO_URI = process.env.MONGO_URI || process.env.MONGODB_URI || 'mongodb://localhost:27017/hiresignal';
const MONGO_DB = process.env.MONGO_DB || 'hiresignal';

conectarMongo(MONGO_URI, MONGO_DB)
  .then(() => {
    createApp().listen(PORT, () => console.log(`Dashboard corriendo en http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.error('No se pudo conectar a MongoDB:', err.message);
    process.exit(1);
  });