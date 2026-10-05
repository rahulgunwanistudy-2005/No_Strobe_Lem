import React, {useState} from 'react';
import {BackHandler, ScrollView, StyleSheet, Text, View} from 'react-native';
import {disclaimer} from '../config';
import {chooseHousehold} from '../settings/preferences';
import type {Preferences} from '../settings/preferences';
import type {CatalogItem} from '../catalog/api';
import {FocusButton} from './FocusButton';
import {ProfilePicker} from './ProfilePicker';
export function Settings({preferences, items, onChange, onBack, message}: {
  preferences: Preferences; items: CatalogItem[]; onChange: (p: Preferences) => void; onBack: () => void; message: string;
}) {
  const [credits, setCredits] = useState(false);
  React.useEffect(() => {
    if (!credits) {return;}
    const back = BackHandler.addEventListener('hardwareBackPress', () => {setCredits(false); return true;});
    return () => back.remove();
  }, [credits]);
  return <ScrollView style={styles.page}>
    <Text style={styles.title}>{credits ? 'Attribution' : 'Viewing settings'}</Text>
    <FocusButton label={credits ? 'Back to settings' : 'Back'} preferred onPress={() => credits ? setCredits(false) : onBack()} />
    {credits ? items.filter((item, i) => items.findIndex(other => other.attribution.credit === item.attribution.credit) === i)
      .map(item => <View key={item.content_id} style={styles.credit}>
        <Text style={styles.body}>{item.attribution.credit}</Text><Text style={styles.body}>{item.attribution.license}</Text>
        <Text selectable style={styles.body}>{item.attribution.url}</Text><Text style={styles.body}>{item.attribution.changes}</Text>
      </View>) : <>
      <Text style={styles.body}>Household · Kids selects the Kids viewing profile automatically.</Text>
      <View style={styles.row}>{(['family', 'kids'] as const).map(value => <FocusButton key={value}
        label={`${preferences.household === value ? '✓ ' : ''}${value === 'family' ? 'Family' : 'Kids household'}`}
        onPress={() => onChange(chooseHousehold(preferences, value))} />)}</View>
      <Text style={styles.body}>Broadcast follows the broadcast area rule. Local uses a smaller viewing area. Kids also softens warnings.</Text>
      <ProfilePicker profile={preferences.profile} kidsHousehold={preferences.household === 'kids'}
        onChange={profile => onChange({...preferences, profile})} />
      <FocusButton label={`Warn me before hazards · ${preferences.warnAhead ? 'On' : 'Off'}`}
        onPress={() => onChange({...preferences, warnAhead: !preferences.warnAhead})} />
      <FocusButton label="Attribution and licenses" onPress={() => setCredits(true)} />
      <Text style={styles.disclaimer}>{disclaimer}</Text>
    </>}
    {!!message && <Text accessibilityRole="alert" style={styles.body}>{message}</Text>}
  </ScrollView>;
}
const styles = StyleSheet.create({page: {flex: 1, backgroundColor: '#0e1823', padding: 40},
  title: {color: '#fff', fontSize: 32, marginBottom: 16}, body: {color: '#c6d3df', fontSize: 19, marginVertical: 10},
  row: {flexDirection: 'row'}, disclaimer: {color: '#c6d3df', fontSize: 18, margin: 12, lineHeight: 26},
  credit: {marginVertical: 16},
});
