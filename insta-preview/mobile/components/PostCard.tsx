import React from 'react';
import {
  View,
  Text,
  Image,
  Dimensions,
  StyleSheet,
  TouchableOpacity,
  useColorScheme,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing } from '../constants/theme';

const SCREEN_WIDTH = Dimensions.get('window').width;

interface PostCardProps {
  imageUrl: string;
  username: string;
  profilePicUrl?: string;
  caption?: string;
  likeCount?: number;
  commentCount?: number;
  isPreview?: boolean;
  aspectRatio?: number;
}

export default function PostCard({
  imageUrl,
  username,
  profilePicUrl,
  caption,
  likeCount = 0,
  commentCount = 0,
  isPreview = false,
  aspectRatio = 1,
}: PostCardProps) {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];
  const styles = makeStyles(colors);

  const imageHeight = Math.min(SCREEN_WIDTH / aspectRatio, SCREEN_WIDTH * 1.25);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        {profilePicUrl ? (
          <Image source={{ uri: profilePicUrl }} style={styles.avatar} />
        ) : (
          <View style={[styles.avatar, styles.avatarPlaceholder]}>
            <Ionicons name="person" size={16} color={colors.textSecondary} />
          </View>
        )}
        <Text style={styles.username}>{username}</Text>
        {isPreview && (
          <View style={styles.previewTag}>
            <Text style={styles.previewTagText}>미리보기</Text>
          </View>
        )}
      </View>

      {/* Image */}
      <Image
        source={{ uri: imageUrl }}
        style={[styles.postImage, { height: imageHeight }]}
        resizeMode="cover"
      />

      {/* Actions */}
      <View style={styles.actions}>
        <View style={styles.leftActions}>
          <TouchableOpacity style={styles.actionBtn}>
            <Ionicons name="heart-outline" size={26} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn}>
            <Ionicons name="chatbubble-outline" size={24} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionBtn}>
            <Ionicons name="paper-plane-outline" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
        <TouchableOpacity>
          <Ionicons name="bookmark-outline" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      {/* Likes */}
      {likeCount > 0 && (
        <Text style={styles.likes}>
          좋아요 {likeCount.toLocaleString()}개
        </Text>
      )}

      {/* Caption */}
      {caption ? (
        <View style={styles.captionRow}>
          <Text style={styles.captionUser}>{username}</Text>
          <Text style={styles.captionText}> {caption}</Text>
        </View>
      ) : null}

      {commentCount > 0 && (
        <Text style={styles.comments}>
          댓글 {commentCount.toLocaleString()}개 모두 보기
        </Text>
      )}
    </View>
  );
}

const makeStyles = (colors: typeof Colors.dark) =>
  StyleSheet.create({
    container: {
      backgroundColor: colors.background,
      marginBottom: 8,
    },
    header: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: Spacing.md,
    },
    avatar: {
      width: 32,
      height: 32,
      borderRadius: 16,
      marginRight: Spacing.sm,
    },
    avatarPlaceholder: {
      backgroundColor: colors.inputBg,
      alignItems: 'center',
      justifyContent: 'center',
    },
    username: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
      flex: 1,
    },
    previewTag: {
      backgroundColor: '#0095f6',
      borderRadius: 4,
      paddingHorizontal: 8,
      paddingVertical: 3,
    },
    previewTagText: {
      color: '#fff',
      fontSize: 11,
      fontWeight: '600',
    },
    postImage: {
      width: SCREEN_WIDTH,
    },
    actions: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.md,
      paddingVertical: Spacing.sm,
    },
    leftActions: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    actionBtn: {
      marginRight: Spacing.lg,
    },
    likes: {
      fontWeight: '600',
      fontSize: 14,
      color: colors.text,
      paddingHorizontal: Spacing.md,
      marginBottom: 4,
    },
    captionRow: {
      flexDirection: 'row',
      paddingHorizontal: Spacing.md,
      flexWrap: 'wrap',
      marginBottom: 4,
    },
    captionUser: {
      fontWeight: '600',
      fontSize: 14,
      color: colors.text,
    },
    captionText: {
      fontSize: 14,
      color: colors.text,
      flex: 1,
    },
    comments: {
      fontSize: 14,
      color: colors.textSecondary,
      paddingHorizontal: Spacing.md,
      marginBottom: Spacing.sm,
    },
  });
