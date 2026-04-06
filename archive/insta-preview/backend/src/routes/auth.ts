import { Router, Request, Response } from 'express';
import { InstagramService } from '../services/instagram';

const router = Router();

router.post('/login', async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      res.status(400).json({ error: 'Username and password are required' });
      return;
    }

    const result = await InstagramService.login(username, password);
    res.json(result);
  } catch (err: any) {
    if (err.message === 'CHECKPOINT_REQUIRED') {
      res.status(403).json({
        error: 'checkpoint_required',
        message: 'Instagram requires verification. Please verify in the Instagram app first.',
      });
      return;
    }
    console.error('Login error:', err.message);
    res.status(401).json({
      error: 'login_failed',
      message: 'Invalid username or password',
    });
  }
});

router.post('/verify-2fa', async (req: Request, res: Response) => {
  try {
    const { sessionId, code, twoFactorIdentifier } = req.body;
    if (!sessionId || !code || !twoFactorIdentifier) {
      res.status(400).json({ error: 'Missing required fields' });
      return;
    }

    await InstagramService.verify2FA(sessionId, code, twoFactorIdentifier);
    res.json({ success: true, sessionId });
  } catch (err: any) {
    console.error('2FA error:', err.message);
    res.status(401).json({ error: '2fa_failed', message: 'Invalid verification code' });
  }
});

router.post('/logout', (req: Request, res: Response) => {
  const sessionId = req.headers['x-session-id'] as string;
  if (sessionId) {
    InstagramService.logout(sessionId);
  }
  res.json({ success: true });
});

export default router;
