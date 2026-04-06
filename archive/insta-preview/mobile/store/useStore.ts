import { create } from 'zustand';
import { api, MediaItem, UserProfile } from '../services/api';

interface AppState {
  isLoggedIn: boolean;
  isLoading: boolean;
  error: string | null;

  // 2FA
  twoFactorRequired: boolean;
  twoFactorIdentifier: string | null;
  pendingSessionId: string | null;

  profile: UserProfile | null;
  feedItems: MediaItem[];

  // 미리보기용 로컬 사진
  previewImages: { uri: string; width: number; height: number }[];

  // 미리보기 모드
  previewMode: 'grid' | 'post';

  login: (username: string, password: string) => Promise<void>;
  verify2FA: (code: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  fetchFeed: () => Promise<void>;
  addPreviewImage: (image: { uri: string; width: number; height: number }) => void;
  removePreviewImage: (index: number) => void;
  clearPreviewImages: () => void;
  setPreviewMode: (mode: 'grid' | 'post') => void;
  clearError: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  isLoggedIn: false,
  isLoading: false,
  error: null,
  twoFactorRequired: false,
  twoFactorIdentifier: null,
  pendingSessionId: null,
  profile: null,
  feedItems: [],
  previewImages: [],
  previewMode: 'grid',

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const result = await api.login(username, password);

      if (result.twoFactorRequired) {
        set({
          isLoading: false,
          twoFactorRequired: true,
          twoFactorIdentifier: result.twoFactorIdentifier || null,
          pendingSessionId: result.sessionId,
        });
        return;
      }

      api.setSessionId(result.sessionId);
      set({ isLoggedIn: true, isLoading: false, twoFactorRequired: false });
    } catch (err: any) {
      const message =
        err.response?.data?.message || err.message || 'Login failed';
      set({ isLoading: false, error: message });
    }
  },

  verify2FA: async (code: string) => {
    const { pendingSessionId, twoFactorIdentifier } = get();
    if (!pendingSessionId || !twoFactorIdentifier) return;

    set({ isLoading: true, error: null });
    try {
      await api.verify2FA(pendingSessionId, code, twoFactorIdentifier);
      api.setSessionId(pendingSessionId);
      set({
        isLoggedIn: true,
        isLoading: false,
        twoFactorRequired: false,
        twoFactorIdentifier: null,
        pendingSessionId: null,
      });
    } catch (err: any) {
      const message =
        err.response?.data?.message || err.message || '2FA verification failed';
      set({ isLoading: false, error: message });
    }
  },

  logout: async () => {
    try {
      await api.logout();
    } catch {}
    set({
      isLoggedIn: false,
      profile: null,
      feedItems: [],
      previewImages: [],
      twoFactorRequired: false,
      twoFactorIdentifier: null,
      pendingSessionId: null,
    });
  },

  fetchProfile: async () => {
    try {
      const profile = await api.getProfile();
      set({ profile });
    } catch (err: any) {
      console.error('Failed to fetch profile:', err.message);
    }
  },

  fetchFeed: async () => {
    set({ isLoading: true });
    try {
      const items = await api.getUserFeed(30);
      set({ feedItems: items, isLoading: false });
    } catch (err: any) {
      set({ isLoading: false, error: 'Failed to load feed' });
    }
  },

  addPreviewImage: (image) => {
    set((state) => ({
      previewImages: [image, ...state.previewImages],
    }));
  },

  removePreviewImage: (index) => {
    set((state) => ({
      previewImages: state.previewImages.filter((_, i) => i !== index),
    }));
  },

  clearPreviewImages: () => set({ previewImages: [] }),

  setPreviewMode: (mode) => set({ previewMode: mode }),

  clearError: () => set({ error: null }),
}));
