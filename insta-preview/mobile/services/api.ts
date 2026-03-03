import axios, { AxiosInstance } from 'axios';

const BASE_URL = 'http://localhost:3000';

class ApiClient {
  private client: AxiosInstance;
  private sessionId: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });

    this.client.interceptors.request.use((config) => {
      if (this.sessionId) {
        config.headers['x-session-id'] = this.sessionId;
      }
      return config;
    });
  }

  setBaseUrl(url: string) {
    this.client.defaults.baseURL = url;
  }

  setSessionId(id: string | null) {
    this.sessionId = id;
  }

  getSessionId() {
    return this.sessionId;
  }

  async login(username: string, password: string) {
    const { data } = await this.client.post<{
      sessionId: string;
      twoFactorRequired?: boolean;
      twoFactorIdentifier?: string;
    }>('/auth/login', { username, password });
    return data;
  }

  async verify2FA(sessionId: string, code: string, twoFactorIdentifier: string) {
    const { data } = await this.client.post<{ success: boolean; sessionId: string }>(
      '/auth/verify-2fa',
      { sessionId, code, twoFactorIdentifier }
    );
    return data;
  }

  async logout() {
    await this.client.post('/auth/logout');
    this.sessionId = null;
  }

  async getProfile() {
    const { data } = await this.client.get<{
      pk: number;
      username: string;
      fullName: string;
      profilePicUrl: string;
      bio: string;
      followerCount: number;
      followingCount: number;
      mediaCount: number;
      isPrivate: boolean;
    }>('/profile/me');
    return data;
  }

  async getUserFeed(limit: number = 30) {
    const { data } = await this.client.get<{
      items: MediaItem[];
    }>('/feed/user', { params: { limit } });
    return data.items;
  }

  async getTimeline(limit: number = 20) {
    const { data } = await this.client.get<{
      items: MediaItem[];
    }>('/feed/timeline', { params: { limit } });
    return data.items;
  }
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

export const api = new ApiClient();
