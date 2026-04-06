import { Router, Request, Response } from 'express';
import { InstagramService } from '../services/instagram';
import { requireSession } from '../middleware/session';

const router = Router();

router.get('/user', requireSession, async (req: Request, res: Response) => {
  try {
    const sessionId = (req as any).sessionId as string;
    const limit = parseInt(req.query.limit as string) || 30;
    const items = await InstagramService.getUserFeed(sessionId, Math.min(limit, 60));
    res.json({ items });
  } catch (err: any) {
    console.error('Feed error:', err.message);
    res.status(500).json({ error: 'Failed to fetch feed' });
  }
});

router.get('/timeline', requireSession, async (req: Request, res: Response) => {
  try {
    const sessionId = (req as any).sessionId as string;
    const limit = parseInt(req.query.limit as string) || 20;
    const items = await InstagramService.getTimeline(sessionId, Math.min(limit, 40));
    res.json({ items });
  } catch (err: any) {
    console.error('Timeline error:', err.message);
    res.status(500).json({ error: 'Failed to fetch timeline' });
  }
});

export default router;
