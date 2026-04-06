import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  FlatList,
  Modal,
  Alert,
  useColorScheme,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing } from '../../constants/theme';
import { useStore } from '../../store/useStore';
import GridView from '../../components/GridView';
import PostCard from '../../components/PostCard';
import PreviewComposer from '../../components/PreviewComposer';

interface LocalPreview {
  uri: string;
  caption: string;
  width: number;
  height: number;
}

export default function PreviewScreen() {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];

  const { feedItems, profile, previewMode, setPreviewMode } = useStore();

  const [localPreviews, setLocalPreviews] = useState<LocalPreview[]>([]);
  const [pendingImage, setPendingImage] = useState<{
    uri: string;
    width: number;
    height: number;
  } | null>(null);

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      setPendingImage({
        uri: asset.uri,
        width: asset.width || 1080,
        height: asset.height || 1080,
      });
    }
  };

  const handleConfirmPreview = (caption: string) => {
    if (!pendingImage) return;
    setLocalPreviews((prev) => [
      { ...pendingImage, caption },
      ...prev,
    ]);
    setPendingImage(null);
  };

  const removePreview = (index: number) => {
    Alert.alert('삭제', '이 미리보기를 삭제하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제',
        style: 'destructive',
        onPress: () => {
          setLocalPreviews((prev) => prev.filter((_, i) => i !== index));
        },
      },
    ]);
  };

  const mergedGridItems = useMemo(() => {
    const previews = localPreviews.map((p, i) => ({
      id: `preview-${i}`,
      imageUrl: p.uri,
      isPreview: true,
    }));
    const existing = feedItems.map((item) => ({
      id: item.id,
      imageUrl: item.thumbnailUrl || item.imageUrl,
      mediaType: item.mediaType,
    }));
    return [...previews, ...existing];
  }, [localPreviews, feedItems]);

  const styles = makeStyles(colors);

  const header = (
    <View>
      {/* Instruction */}
      <View style={styles.instructionBox}>
        <Ionicons name="eye" size={20} color={colors.primary} />
        <Text style={styles.instructionText}>
          새 사진을 추가하면 피드에서 어떻게 보이는지 확인할 수 있습니다.
          파란 테두리가 미리보기 사진입니다.
        </Text>
      </View>

      {/* Preview count & controls */}
      <View style={styles.controls}>
        <View style={styles.controlLeft}>
          <Text style={styles.previewCount}>
            미리보기 {localPreviews.length}장
          </Text>
          {localPreviews.length > 0 && (
            <TouchableOpacity
              style={styles.clearBtn}
              onPress={() => {
                Alert.alert('전체 삭제', '모든 미리보기를 삭제하시겠습니까?', [
                  { text: '취소', style: 'cancel' },
                  {
                    text: '삭제',
                    style: 'destructive',
                    onPress: () => setLocalPreviews([]),
                  },
                ]);
              }}
            >
              <Text style={styles.clearBtnText}>전체 삭제</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* View mode toggle */}
        <View style={styles.modeToggle}>
          <TouchableOpacity
            style={[
              styles.modeBtn,
              previewMode === 'grid' && styles.modeBtnActive,
            ]}
            onPress={() => setPreviewMode('grid')}
          >
            <Ionicons
              name="grid"
              size={18}
              color={previewMode === 'grid' ? '#fff' : colors.textSecondary}
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.modeBtn,
              previewMode === 'post' && styles.modeBtnActive,
            ]}
            onPress={() => setPreviewMode('post')}
          >
            <Ionicons
              name="square"
              size={18}
              color={previewMode === 'post' ? '#fff' : colors.textSecondary}
            />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <Text style={styles.topBarTitle}>미리보기</Text>
        <TouchableOpacity style={styles.addButton} onPress={pickImage}>
          <Ionicons name="add" size={22} color="#fff" />
          <Text style={styles.addButtonText}>사진 추가</Text>
        </TouchableOpacity>
      </View>

      {/* Content: Grid or Post mode */}
      {previewMode === 'grid' ? (
        <GridView
          items={mergedGridItems}
          ListHeaderComponent={header}
          onItemPress={(item, index) => {
            if (item.isPreview) {
              const previewIndex = localPreviews.findIndex(
                (_, i) => `preview-${i}` === item.id
              );
              if (previewIndex >= 0) removePreview(previewIndex);
            }
          }}
        />
      ) : (
        <FlatList
          data={[header]}
          keyExtractor={() => 'header'}
          renderItem={() => header}
          ListFooterComponent={
            <>
              {localPreviews.map((p, i) => (
                <PostCard
                  key={`preview-post-${i}`}
                  imageUrl={p.uri}
                  username={profile?.username || 'me'}
                  profilePicUrl={profile?.profilePicUrl}
                  caption={p.caption}
                  isPreview
                  aspectRatio={p.width / p.height}
                />
              ))}
              {feedItems.map((item) => (
                <PostCard
                  key={item.id}
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
              ))}
            </>
          }
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Composer Modal */}
      <Modal
        visible={pendingImage !== null}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        {pendingImage && (
          <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
            <PreviewComposer
              imageUri={pendingImage.uri}
              onConfirm={handleConfirmPreview}
              onCancel={() => setPendingImage(null)}
            />
          </SafeAreaView>
        )}
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
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    topBarTitle: {
      fontSize: 20,
      fontWeight: '700',
      color: colors.text,
    },
    addButton: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: colors.primary,
      borderRadius: 8,
      paddingHorizontal: 14,
      paddingVertical: 8,
      gap: 4,
    },
    addButtonText: {
      color: '#fff',
      fontSize: 14,
      fontWeight: '600',
    },
    instructionBox: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      backgroundColor: colors.surface,
      marginHorizontal: Spacing.lg,
      marginTop: Spacing.md,
      padding: Spacing.md,
      borderRadius: 10,
      gap: 10,
    },
    instructionText: {
      flex: 1,
      fontSize: 13,
      color: colors.textSecondary,
      lineHeight: 19,
    },
    controls: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
    },
    controlLeft: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: Spacing.md,
    },
    previewCount: {
      fontSize: 14,
      fontWeight: '600',
      color: colors.text,
    },
    clearBtn: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 4,
      backgroundColor: colors.surface,
    },
    clearBtnText: {
      fontSize: 12,
      color: colors.error,
      fontWeight: '500',
    },
    modeToggle: {
      flexDirection: 'row',
      backgroundColor: colors.surface,
      borderRadius: 8,
      overflow: 'hidden',
    },
    modeBtn: {
      paddingHorizontal: 12,
      paddingVertical: 8,
    },
    modeBtnActive: {
      backgroundColor: colors.primary,
      borderRadius: 6,
    },
  });
