import React from 'react';
import {
  View,
  Image,
  FlatList,
  Dimensions,
  StyleSheet,
  TouchableOpacity,
  useColorScheme,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/theme';
import { MediaItem } from '../services/api';

const SCREEN_WIDTH = Dimensions.get('window').width;
const GAP = 2;
const ITEM_SIZE = (SCREEN_WIDTH - GAP * 2) / 3;

interface GridItem {
  id: string;
  imageUrl: string;
  isPreview?: boolean;
  mediaType?: 'image' | 'video' | 'carousel';
}

interface GridViewProps {
  items: GridItem[];
  onItemPress?: (item: GridItem, index: number) => void;
  ListHeaderComponent?: React.ReactElement;
}

export default function GridView({ items, onItemPress, ListHeaderComponent }: GridViewProps) {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];

  const renderItem = ({ item, index }: { item: GridItem; index: number }) => (
    <TouchableOpacity
      style={[
        styles.item,
        { backgroundColor: colors.card },
        item.isPreview && styles.previewItem,
      ]}
      activeOpacity={0.8}
      onPress={() => onItemPress?.(item, index)}
    >
      <Image source={{ uri: item.imageUrl }} style={styles.image} />
      {item.isPreview && (
        <View style={styles.previewBadge}>
          <Ionicons name="eye" size={14} color="#fff" />
        </View>
      )}
      {item.mediaType === 'carousel' && (
        <View style={styles.carouselBadge}>
          <Ionicons name="copy-outline" size={14} color="#fff" />
        </View>
      )}
      {item.mediaType === 'video' && (
        <View style={styles.carouselBadge}>
          <Ionicons name="play" size={14} color="#fff" />
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <FlatList
      data={items}
      renderItem={renderItem}
      keyExtractor={(item, i) => `${item.id}-${i}`}
      numColumns={3}
      columnWrapperStyle={styles.row}
      ListHeaderComponent={ListHeaderComponent}
      showsVerticalScrollIndicator={false}
    />
  );
}

const styles = StyleSheet.create({
  row: {
    gap: GAP,
    marginBottom: GAP,
  },
  item: {
    width: ITEM_SIZE,
    height: ITEM_SIZE,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  previewItem: {
    borderWidth: 2,
    borderColor: '#0095f6',
  },
  previewBadge: {
    position: 'absolute',
    top: 6,
    left: 6,
    backgroundColor: '#0095f6',
    borderRadius: 10,
    width: 22,
    height: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  carouselBadge: {
    position: 'absolute',
    top: 6,
    right: 6,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 10,
    width: 22,
    height: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
