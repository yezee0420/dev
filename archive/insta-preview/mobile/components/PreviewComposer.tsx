import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  useColorScheme,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Spacing } from '../constants/theme';

const SCREEN_WIDTH = Dimensions.get('window').width;

interface PreviewComposerProps {
  imageUri: string;
  onConfirm: (caption: string) => void;
  onCancel: () => void;
}

export default function PreviewComposer({
  imageUri,
  onConfirm,
  onCancel,
}: PreviewComposerProps) {
  const colorScheme = useColorScheme();
  const colors = Colors[colorScheme === 'dark' ? 'dark' : 'light'];
  const [caption, setCaption] = useState('');
  const styles = makeStyles(colors);

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <View style={styles.header}>
        <TouchableOpacity onPress={onCancel}>
          <Ionicons name="close" size={28} color={colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>새 미리보기</Text>
        <TouchableOpacity onPress={() => onConfirm(caption)}>
          <Text style={styles.doneText}>추가</Text>
        </TouchableOpacity>
      </View>

      <Image
        source={{ uri: imageUri }}
        style={styles.preview}
        resizeMode="cover"
      />

      <View style={styles.captionSection}>
        <TextInput
          style={styles.captionInput}
          placeholder="캡션을 입력하세요... (선택)"
          placeholderTextColor={colors.placeholder}
          value={caption}
          onChangeText={setCaption}
          multiline
          numberOfLines={3}
        />
      </View>

      <Text style={styles.hint}>
        이 사진은 실제로 업로드되지 않습니다.{'\n'}
        피드에서 어떻게 보일지 미리보기 전용입니다.
      </Text>
    </ScrollView>
  );
}

const makeStyles = (colors: typeof Colors.dark) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: colors.background,
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    title: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
    },
    doneText: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.primary,
    },
    preview: {
      width: SCREEN_WIDTH,
      height: SCREEN_WIDTH,
    },
    captionSection: {
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      borderBottomWidth: 0.5,
      borderBottomColor: colors.separator,
    },
    captionInput: {
      fontSize: 15,
      color: colors.text,
      minHeight: 60,
      textAlignVertical: 'top',
    },
    hint: {
      textAlign: 'center',
      color: colors.placeholder,
      fontSize: 12,
      marginTop: Spacing.xl,
      lineHeight: 18,
    },
  });
