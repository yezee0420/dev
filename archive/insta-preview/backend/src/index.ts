import express from 'express';
import cors from 'cors';
import authRoutes from './routes/auth';
import feedRoutes from './routes/feed';
import profileRoutes from './routes/profile';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/feed', feedRoutes);
app.use('/profile', profileRoutes);

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
