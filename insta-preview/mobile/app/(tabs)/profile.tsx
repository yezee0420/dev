import React, { useEffect } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  useColorScheme,
  SafeAreaView,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Colors, Spacing } from '../../constants/theme';
import { useStore } from '../../store/useStore';
import GridView from '../../components/GridView';

export default function ProfileScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];

  const { profile, feedItems, isLoading, fetchProfile, fetchFeed, logout } =
    useStore();

  useEffect(() => {
    if (!profile) fetchProfile();
    if (feedItems.length === 0) fetchFeed();
  }, []);

  const handleLogout = () => {
    Alert.alert('로그아웃', '정말 로그아웃 하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await logout();
          router.replace('/');
        },
      },
    ]);
  };

  const styles = makeStyles(colors);

  const gridItems = feedItems.map((item) => ({
    id: item.id,
    imageUrl: item.thumbnailUrl || item.imageUrl,
    mediaType: item.mediaType,
  }));

  const formatCount = (n: number): string => {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 10_000) return (n / 1000).toFixed(1) + 'K';
    if (n >= 1_000) return n.toLocaleString();
    return n.toString();
  };

  const profileHeader = profile ? (
    <View>
      {/* Profile Info */}
      <View style={styles.profileSection}>
        {profile.profilePicUrl ? (
          <Image
            source={{ uri: profile.profilePicUrl }}
            style={styles.profilePic}
          />
        ) : (
          <View style={[styles.profilePic, styles.profilePicPlaceholder]}>
            <Ionicons name="person" size={40} color={colors.textSecondary} />
          </View>
        )}

        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>
              {formatCount(profile.mediaCount)}
            </Text>
            <Text style={styles.statLabel}>게시물</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>
              {formatCount(profile.followerCount)}
            </Text>
            <Text style={styles.statLabel}>팔로워</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statNumber}>
              {formatCount(profile.followingCount)}
            </Text>
            <Text style={styles.statLabel}>팔로잉</Text>
          </View>
        </View>
      </View>

      {/* Name & Bio */}
      <View style={styles.bioSection}>
        {profile.fullName ? (
          <Text style={styles.fullName}>{profile.fullName}</Text>
        ) : null}
        {profile.bio ? (
          <Text style={styles.bio}>{profile.bio}</Text>
        ) : null}
      </View>

      {/* Divider */}
      <View style={styles.divider} />
    </View>
  ) : null;

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <Text style={styles.usernameTitle}>{profile?.username || '...'}</Text>
        <TouchableOpacity onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      {isLoading && !profile ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : (
        <GridView items={gridItems} ListHeaderComponent={profileHeader!} />
      )}
    </SafeAreaView>
  );
}

const makeStyles = (colors: typeof Colors.dark) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    topBar: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    usernameTitle: {
      fontSize: 20,
      fontWeight: '700',
      color: colors.text,
    },
    profileSection: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.lg,
    },
    profilePic: {
      width: 80,
      height: 80,
      borderRadius: 40,
    },
    profilePicPlaceholder: {
      backgroundColor: colors.inputBg,
      alignItems: 'center',
      justifyContent: 'center',
    },
    statsRow: {
      flex: 1,
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginLeft: Spacing.xl,
    },
    statItem: {
      alignItems: 'center',
    },
    statNumber: {
      fontSize: 18,
      fontWeight: '700',
      color: colors.text,
    },
    statLabel: {
      fontSize: 13,
      color: colors.textSecondary,
      marginTop: 2,
    },
    bioSection: {
      paddingHorizontal: Spacing.lg,
      paddingBottom: Spacing.md,
    },
    fullName: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 2,
    },
    bio: {
      fontSize: 14,
      color: colors.text,
      lineHeight: 20,
    },
    divider: {
      height: 0.5,
      backgroundColor: colors.separator,
      marginTop: Spacing.sm,
    },
    center: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
  });
