import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { assertRuntimeSecrets, env } from './config/env.js';
import searchRoutes from './routes/searchRoutes.js';
import { errorHandler, notFoundHandler } from './middleware/errorHandler.js';

assertRuntimeSecrets();

const app = express();

app.use(helmet());
app.use(
  cors({
    origin: env.clientOrigin,
    methods: ['GET', 'POST', 'OPTIONS'],
  }),
);
app.use(express.json({ limit: '1mb' }));

app.get('/', (_req, res) => {
  res.json({
    name: 'AI YouTube Semantic Search API',
    version: '1.0.0',
    endpoints: {
      health: 'GET /api/health',
      search: 'POST /api/search',
    },
  });
});

app.use('/api', searchRoutes);

app.use(notFoundHandler);
app.use(errorHandler);

app.listen(env.port, () => {
  console.log(`API listening on http://localhost:${env.port}`);
  console.log(`CORS origin: ${env.clientOrigin}`);
});

export default app;
