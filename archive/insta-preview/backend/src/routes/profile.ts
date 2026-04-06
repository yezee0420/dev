import { Router, Request, Response } from 'express';
import { InstagramService } from '../services/instagram';
import { requireSession } from '../middleware/session';

const router = Router();

router.get('/me', requireSession, async (req: Request, res: Response) => {
  try {
    const sessionId = (req as any).sessionId as string;
    const profile = await InstagramService.getProfile(sessionId);
    res.json(profile);
  } catch (err: any) {
    console.error('Profile error:', err.message);
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});

export default router;
