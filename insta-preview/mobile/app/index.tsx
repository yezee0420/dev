import { useEffect } from 'react';
import { router } from 'expo-router';
import { useStore } from '../store/useStore';
import LoginScreen from './login';

export default function Index() {
  const isLoggedIn = useStore((s) => s.isLoggedIn);

  useEffect(() => {
    if (isLoggedIn) {
      router.replace('/(tabs)/feed');
    }
  }, [isLoggedIn]);

  return <LoginScreen />;
}
