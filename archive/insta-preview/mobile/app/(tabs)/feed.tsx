import React, { useEffect, useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  useColorScheme,
  Modal,
  FlatList,
  SafeAreaView,
} from 'react-native';
import { Colors, Spacing } from '../../constants/theme';
import { useStore } from '../../store/useStore';
import GridView from '../../components/GridView';
import PostCard from '../../components/PostCard';

export default function FeedScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];

  const { feedItems, isLoading, profile, fetchFeed, fetchProfile } = useStore();
  const [refreshing, setRefreshing] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  useEffect(() => {
    fetchProfile();
    fetchFeed();
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchFeed();
    setRefreshing(false);
  }, []);

  const gridItems = feedItems.map((item) => ({
    id: item.id,
    imageUrl: item.thumbnailUrl || item.imageUrl,
    mediaType: item.mediaType,
  }));

  const styles = makeStyles(colors);

  const header = (
    <View style={styles.header}>
      <Text style={styles.headerTitle}>내 게시물</Text>
      <Text style={styles.headerCount}>{feedItems.length}개</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.logo}>InstaPreview</Text>
      </View>

      {isLoading && feedItems.length === 0 ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>피드를 불러오는 중...</Text>
        </View>
      ) : feedItems.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>게시물이 없습니다</Text>
        </View>
      ) : (
        <GridView
          items={gridItems}
          onItemPress={(item, index) => setSelectedIndex(index)}
          ListHeaderComponent={header}
        />
      )}

      {/* Post Detail Modal */}
      <Modal
        visible={selectedIndex !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelectedIndex(null)}
      >
        <SafeAreaView style={styles.modal}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>게시물</Text>
            <Text
              style={styles.modalClose}
              onPress={() => setSelectedIndex(null)}
            >
              닫기
            </Text>
          </View>
          {selectedIndex !== null && (
            <FlatList
              data={feedItems.slice(selectedIndex)}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <PostCard
                  imageUrl={item.imageUrl}
                  username={profile?.username || ''}
                  profilePicUrl={profile?.profilePicUrl}
                  caption={item.caption}
                  likeCount={item.likeCount}
                  commentCount={item.commentCount}
                  aspectRatio={
                    item.width && item.height ? item.width / item.height : 1
                  }
                />
              )}
              showsVerticalScrollIndicator={false}
            />
          )}
        </SafeAreaView>
      </Modal>
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
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    logo: {
      fontSize: 22,
      fontWeight: '700',
      fontStyle: 'italic',
      color: colors.text,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
    },
    headerTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
    },
    headerCount: {
      fontSize: 14,
      color: colors.textSecondary,
    },
    center: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    loadingText: {
      marginTop: Spacing.md,
      color: colors.textSecondary,
      fontSize: 14,
    },
    emptyText: {
      color: colors.textSecondary,
      fontSize: 16,
    },
    modal: {
      flex: 1,
      backgroundColor: colors.background,
    },
    modalHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
    },
    modalClose: {
      fontSize: 16,
      color: colors.primary,
      fontWeight: '500',
    },
  });
