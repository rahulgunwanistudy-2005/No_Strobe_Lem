import React from 'react';
import {StyleSheet, View} from 'react-native';
import type {Profile} from '../types/hazardtrack';
import {FocusButton} from './FocusButton';
export function ProfilePicker({profile, kidsHousehold, onChange}: {profile: Profile; kidsHousehold: boolean; onChange: (profile: Profile) => void}) {
  return <View style={styles.row}>{(['broadcast', 'local', 'kids'] as const).map(value =>
    <FocusButton key={value} label={`${profile === value ? '✓ ' : ''}${value[0].toUpperCase() + value.slice(1)}`}
      disabled={kidsHousehold && value !== 'kids'} onPress={() => onChange(value)} />)}</View>;
}

const styles = StyleSheet.create({row: {flexDirection: 'row'}});
