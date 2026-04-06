import {
  IgApiClient,
  IgLoginTwoFactorRequiredError,
  IgCheckpointError,
} from 'instagram-private-api';
import { v4 as uuidv4 } from 'uuid';

export interface IgSession {
  id: string;
  client: IgApiClient;
  userId: number;
  username: string;
}

export interface MediaItem {
  id: string;
  imageUrl: string;
  thumbnailUrl: string;
  width: number;
  height: number;
  likeCount: number;
  commentCount: number;
  caption: string;
  takenAt: number;
  mediaType: 'image' | 'video' | 'carousel';
  carouselMedia?: { imageUrl: string; width: number; height: number }[];
}

export interface UserProfile {
  pk: number;
  username: string;
  fullName: string;
  profilePicUrl: string;
  bio: string;
  followerCount: number;
  followingCount: number;
  mediaCount: number;
  isPrivate: boolean;
}

const sessions = new Map<string, IgSession>();

function extractBestImage(candidates: any[]): { url: string; width: number; height: number } {
  if (!candidates || candidates.length === 0) {
    return { url: '', width: 0, height: 0 };
  }
  const best = candidates[0];
  return { url: best.url, width: best.width, height: best.height };
}

function parseMediaItem(item: any): MediaItem {
  const bestImage = extractBestImage(item.image_versions2?.candidates);
  let mediaType: MediaItem['mediaType'] = 'image';
  if (item.media_type === 2) mediaType = 'video';
  if (item.media_type === 8) mediaType = 'carousel';

  let carouselMedia: MediaItem['carouselMedia'];
  if (mediaType === 'carousel' && item.carousel_media) {
    carouselMedia = item.carousel_media.map((cm: any) => {
      const img = extractBestImage(cm.image_versions2?.candidates);
      return { imageUrl: img.url, width: img.width, height: img.height };
    });
  }

  return {
    id: item.pk?.toString() || item.id,
    imageUrl: bestImage.url,
    thumbnailUrl: bestImage.url,
    width: bestImage.width,
    height: bestImage.height,
    likeCount: item.like_count || 0,
    commentCount: item.comment_count || 0,
    caption: item.caption?.text || '',
    takenAt: item.taken_at || 0,
    mediaType,
    carouselMedia,
  };
}

export class InstagramService {
  static getSession(sessionId: string): IgSession | undefined {
    return sessions.get(sessionId);
  }

  static async login(
    username: string,
    password: string
  ): Promise<{ sessionId: string; twoFactorRequired?: boolean; twoFactorIdentifier?: string }> {
    const ig = new IgApiClient();
    ig.state.generateDevice(username);

    try {
      const auth = await ig.account.login(username, password);
      const sessionId = uuidv4();
      sessions.set(sessionId, {
        id: sessionId,
        client: ig,
        userId: auth.pk,
        username: auth.username,
      });
      return { sessionId };
    } catch (err) {
      if (err instanceof IgLoginTwoFactorRequiredError) {
        const twoFactorInfo = err.response.body.two_factor_info;
        const sessionId = uuidv4();
        // Store the client temporarily for 2FA completion
        sessions.set(sessionId, {
          id: sessionId,
          client: ig,
          userId: 0,
          username,
        });
        return {
          sessionId,
          twoFactorRequired: true,
          twoFactorIdentifier: twoFactorInfo.two_factor_identifier,
        };
      }
      if (err instanceof IgCheckpointError) {
        await ig.challenge.auto(true);
        throw new Error('CHECKPOINT_REQUIRED');
      }
      throw err;
    }
  }

  static async verify2FA(
    sessionId: string,
    code: string,
    twoFactorIdentifier: string
  ): Promise<boolean> {
    const session = sessions.get(sessionId);
    if (!session) throw new Error('SESSION_NOT_FOUND');

    const auth = await session.client.account.twoFactorLogin({
      username: session.username,
      verificationCode: code,
      twoFactorIdentifier,
      verificationMethod: '1',
      trustThisDevice: '1',
    });

    session.userId = auth.pk;
    session.username = auth.username;
    return true;
  }

  static async getProfile(sessionId: string): Promise<UserProfile> {
    const session = sessions.get(sessionId);
    if (!session) throw new Error('SESSION_NOT_FOUND');

    const ig = session.client;
    const user = await ig.user.info(session.userId);

    return {
      pk: user.pk,
      username: user.username,
      fullName: user.full_name,
      profilePicUrl: user.profile_pic_url,
      bio: user.biography,
      followerCount: user.follower_count,
      followingCount: user.following_count,
      mediaCount: user.media_count,
      isPrivate: user.is_private,
    };
  }

  static async getUserFeed(
    sessionId: string,
    maxItems: number = 30
  ): Promise<MediaItem[]> {
    const session = sessions.get(sessionId);
    if (!session) throw new Error('SESSION_NOT_FOUND');

    const ig = session.client;
    const feed = ig.feed.user(session.userId);
    const items: MediaItem[] = [];

    let page = await feed.items();
    for (const item of page) {
      items.push(parseMediaItem(item));
      if (items.length >= maxItems) break;
    }

    if (items.length < maxItems && feed.isMoreAvailable()) {
      page = await feed.items();
      for (const item of page) {
        items.push(parseMediaItem(item));
        if (items.length >= maxItems) break;
      }
    }

    return items.slice(0, maxItems);
  }

  static async getTimeline(
    sessionId: string,
    maxItems: number = 20
  ): Promise<MediaItem[]> {
    const session = sessions.get(sessionId);
    if (!session) throw new Error('SESSION_NOT_FOUND');

    const ig = session.client;
    const feed = ig.feed.timeline();
    const items: MediaItem[] = [];

    const page = await feed.items();
    for (const item of page) {
      if (item.image_versions2) {
        items.push(parseMediaItem(item));
        if (items.length >= maxItems) break;
      }
    }

    return items.slice(0, maxItems);
  }

  static logout(sessionId: string): void {
    sessions.delete(sessionId);
  }
}
