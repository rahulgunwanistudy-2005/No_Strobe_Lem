import React from 'react';
import {AccessibilityInfo, StyleSheet, Text, View} from 'react-native';
import {FocusButton} from './FocusButton';
import type {HazardSegment} from './hazards';
export function HazardAheadChip({segment, onSkip, disabled}: {segment?: HazardSegment; onSkip: () => void; disabled: boolean}) {
  React.useEffect(() => {
    if (segment) {AccessibilityInfo.announceForAccessibility('Flashing ahead. Press OK on the skip button to skip.');}
  }, [segment?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!segment) {return null;}
  return <View style={styles.chip}>
    <FocusButton label="Flashing ahead · OK to skip" onPress={onSkip} disabled={disabled} />
    {segment.kind === 'unresolved' && <Text style={styles.label}>Reduction unresolved. Skip this segment.</Text>}
  </View>;
}

const styles = StyleSheet.create({chip: {backgroundColor: '#202c3a', borderRadius: 12}, label: {color: '#fff', padding: 12}});
