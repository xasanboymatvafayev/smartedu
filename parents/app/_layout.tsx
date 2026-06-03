import { Stack } from 'expo-router';
import { useEffect } from 'react';
import * as SplashScreen from 'expo-splash-screen';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { Asset } from 'expo-asset';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  useEffect(() => {
    async function prepare() {
      try {
        await Asset.loadAsync([
          require('../assets/images/icon.png'),
          require('../assets/images/adaptive-icon.png'),
          require('../assets/images/favicon.png'),
        ]);
        await SplashScreen.hideAsync();
      } catch (e) { console.warn(e); }
    }
    prepare();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="student-dashboard" />
        <Stack.Screen name="student-calendar" />
        <Stack.Screen name="student-ranking" />
        <Stack.Screen name="student-store" />
        <Stack.Screen name="student-profile" />
      </Stack>
    </GestureHandlerRootView>
  );
}
