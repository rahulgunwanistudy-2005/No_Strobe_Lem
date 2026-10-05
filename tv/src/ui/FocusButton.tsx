import React, {useState} from 'react';
import {Pressable, StyleSheet, Text} from 'react-native';
import type {ReactNode} from 'react';
export function FocusButton({label, onPress, preferred = false, disabled = false, children, onFocus, onBlur}: {
  label: string; onPress: () => void; preferred?: boolean; disabled?: boolean;
  children?: ReactNode; onFocus?: () => void; onBlur?: () => void;
}) {
  const [focused, setFocused] = useState(false);
  return <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled}
    hasTVPreferredFocus={preferred} onPress={onPress}
    onFocus={() => {setFocused(true); onFocus?.();}} onBlur={() => {setFocused(false); onBlur?.();}}
    style={[styles.button, focused && styles.focus, disabled && styles.disabled]}>
    {children ?? <Text style={styles.text}>{label}</Text>}
  </Pressable>;
}
const styles = StyleSheet.create({
  button: {padding: 14, margin: 6, backgroundColor: '#202c3a', borderWidth: 3, borderColor: '#364556', borderRadius: 10},
  focus: {borderColor: '#8cf0d1', backgroundColor: '#304858'},
  disabled: {opacity: 0.45}, text: {color: '#fff', fontSize: 20},
});
