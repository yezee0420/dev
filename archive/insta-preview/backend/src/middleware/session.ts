import { Request, Response, NextFunction } from 'express';
import { InstagramService } from '../services/instagram';

export function requireSession(req: Request, res: Response, next: NextFunction) {
  const sessionId = req.headers['x-session-id'] as string;
  if (!sessionId) {
    res.status(401).json({ error: 'No session ID provided' });
    return;
  }

  const session = InstagramService.getSession(sessionId);
  if (!session) {
    res.status(401).json({ error: 'Invalid or expired session' });
    return;
  }

  (req as any).sessionId = sessionId;
  (req as any).igSession = session;
  next();
}
