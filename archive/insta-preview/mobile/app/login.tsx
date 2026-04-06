import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  useColorScheme,
  Alert,
} from 'react-native';
import { Colors, Spacing } from '../constants/theme';
import { useStore } from '../store/useStore';
import { api } from '../services/api';

export default function LoginScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [serverUrl, setServerUrl] = useState('http://localhost:3000');
  const [showSettings, setShowSettings] = useState(false);

  const {
    isLoading,
    error,
    twoFactorRequired,
    login,
    verify2FA,
    clearError,
  } = useStore();

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      Alert.alert('오류', '아이디와 비밀번호를 입력해주세요.');
      return;
    }
    api.setBaseUrl(serverUrl);
    clearError();
    await login(username.trim(), password.trim());
  };

  const handle2FA = async () => {
    if (!twoFactorCode.trim()) {
      Alert.alert('오류', '인증 코드를 입력해주세요.');
      return;
    }
    await verify2FA(twoFactorCode.trim());
  };

  const styles = makeStyles(colors);

  if (twoFactorRequired) {
    return (
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.content}>
          <Text style={styles.logo}>InstaPreview</Text>
          <Text style={styles.subtitle}>2단계 인증</Text>
          <Text style={styles.description}>
            인스타그램 앱이나 SMS로 전송된 인증 코드를 입력하세요.
          </Text>

          <TextInput
            style={styles.input}
            placeholder="인증 코드"
            placeholderTextColor={colors.placeholder}
            value={twoFactorCode}
            onChangeText={setTwoFactorCode}
            keyboardType="number-pad"
            autoFocus
          />

          {error && <Text style={styles.error}>{error}</Text>}

          <TouchableOpacity
            style={[styles.button, isLoading && styles.buttonDisabled]}
            onPress={handle2FA}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>확인</Text>
            )}
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        <Text style={styles.logo}>InstaPreview</Text>
        <Text style={styles.subtitle}>
          인스타그램 피드 미리보기
        </Text>

        <TextInput
          style={styles.input}
          placeholder="인스타그램 아이디"
          placeholderTextColor={colors.placeholder}
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <TextInput
          style={styles.input}
          placeholder="비밀번호"
          placeholderTextColor={colors.placeholder}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />

        {error && <Text style={styles.error}>{error}</Text>}

        <TouchableOpacity
          style={[
            styles.button,
            (isLoading || !username || !password) && styles.buttonDisabled,
          ]}
          onPress={handleLogin}
          disabled={isLoading || !username || !password}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>로그인</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.settingsToggle}
          onPress={() => setShowSettings(!showSettings)}
        >
          <Text style={styles.settingsText}>
            {showSettings ? '서버 설정 닫기' : '서버 설정'}
          </Text>
        </TouchableOpacity>

        {showSettings && (
          <View style={styles.settingsBox}>
            <Text style={styles.settingsLabel}>Backend URL</Text>
            <TextInput
              style={styles.input}
              placeholder="http://localhost:3000"
              placeholderTextColor={colors.placeholder}
              value={serverUrl}
              onChangeText={setServerUrl}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
          </View>
        )}

        <Text style={styles.warning}>
          ⚠ 비공식 API를 사용합니다. 계정 제한 위험이 있으니{'\n'}
          개인 용도로만 사용하세요.
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const makeStyles = (colors: typeof Colors.dark) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    content: {
      flex: 1,
      justifyContent: 'center',
      paddingHorizontal: 40,
    },
    logo: {
      fontSize: 36,
      fontWeight: '700',
      color: colors.text,
      textAlign: 'center',
      marginBottom: Spacing.sm,
      fontStyle: 'italic',
    },
    subtitle: {
      fontSize: 15,
      color: colors.textSecondary,
      textAlign: 'center',
      marginBottom: Spacing.xxl,
    },
    description: {
      fontSize: 14,
      color: colors.textSecondary,
      textAlign: 'center',
      marginBottom: Spacing.lg,
      lineHeight: 20,
    },
    input: {
      backgroundColor: colors.inputBg,
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 8,
      paddingHorizontal: Spacing.lg,
      paddingVertical: 14,
      fontSize: 15,
      color: colors.text,
      marginBottom: Spacing.md,
    },
    button: {
      backgroundColor: colors.primary,
      borderRadius: 8,
      paddingVertical: 14,
      alignItems: 'center',
      marginTop: Spacing.sm,
    },
    buttonDisabled: {
      opacity: 0.5,
    },
    buttonText: {
      color: '#ffffff',
      fontSize: 16,
      fontWeight: '600',
    },
    error: {
      color: colors.error,
      fontSize: 13,
      textAlign: 'center',
      marginBottom: Spacing.sm,
    },
    settingsToggle: {
      marginTop: Spacing.lg,
      alignItems: 'center',
    },
    settingsText: {
      color: colors.textSecondary,
      fontSize: 13,
    },
    settingsBox: {
      marginTop: Spacing.md,
    },
    settingsLabel: {
      color: colors.textSecondary,
      fontSize: 12,
      marginBottom: Spacing.xs,
    },
    warning: {
      marginTop: Spacing.xxl,
      fontSize: 11,
      color: colors.placeholder,
      textAlign: 'center',
      lineHeight: 17,
    },
  });
