import 'dotenv/config';

import createApp, { conectarMongo, MONGO_URI, MONGO_DB } from './app.js';

const PORT = Number(process.env.PORT) || 3000;

conectarMongo(MONGO_URI, MONGO_DB)
  .then(() => {
    createApp().listen(PORT, () => console.log(`Dashboard corriendo en http://localhost:${PORT}`));
  })
  .catch((err) => {
    console.error('No se pudo conectar a MongoDB:', err.message);
    process.exit(1);
  });