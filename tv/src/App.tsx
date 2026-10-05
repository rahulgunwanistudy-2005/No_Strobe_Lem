import React, {useEffect, useState} from 'react';
import {BackHandler, StyleSheet, Text, View} from 'react-native';
import {loadCatalog} from './catalog/api';
import type {CatalogItem} from './catalog/api';
import {defaultPreferences, PreferenceStore} from './settings/preferences';
import type {Preferences} from './settings/preferences';
import {Catalog} from './ui/Catalog';
import {FocusButton} from './ui/FocusButton';
import {PlayerScreen} from './ui/PlayerScreen';
import {Settings} from './ui/Settings';

export function App() {
  const [store] = useState(() => new PreferenceStore());
  const [preferences, setPreferences] = useState(defaultPreferences);
  const [settingsReady, setSettingsReady] = useState(false);
  const [message, setMessage] = useState('');
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [catalogReady, setCatalogReady] = useState(false);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [selected, setSelected] = useState<CatalogItem>();
  const [selectedId, setSelectedId] = useState<string>();
  const [settings, setSettings] = useState(false);
  const [revision, setRevision] = useState(0);
  const [calibration, setCalibration] = useState<'sync' | 'compositing'>();
  useEffect(() => {
    let live = true;
    store.load().then(value => {if (live) {setPreferences(value);}})
      .catch(() => {if (live) {setMessage('Saved settings could not be read. Choose a household and profile before playback.'); setSettings(true);}})
      .finally(() => {if (live) {setSettingsReady(true);}});
    return () => {live = false;};
  }, [store]);
  useEffect(() => {
    let live = true;
    const abort = new AbortController();
    setError(''); setCatalogReady(false);
    loadCatalog(abort.signal).then(value => {if (live) {setItems(value); setCatalogReady(true);}})
      .catch(failure => {if (live) {setError(failure instanceof Error ? failure.message : 'Network error. Please retry.');}});
    return () => {live = false; abort.abort();};
  }, [attempt]);
  useEffect(() => {
    const back = BackHandler.addEventListener('hardwareBackPress', () => {
      if (calibration) {setCalibration(undefined); return true;}
      if (settings) {setSettings(false); return true;}
      if (selected) {setSelected(undefined); return true;}
      return false;
    });
    return () => back.remove();
  }, [settings, selected, calibration]);
  const changePreferences = (value: Preferences) => {
    setPreferences(value); setMessage('');
    store.save(value).catch(() => setMessage('Settings could not be saved. Your current choice applies until the app closes.'));
  };
  if (__DEV__ && calibration) {
    const {CalibrationScreen} = require('./calibration/CalibrationScreen') as typeof import('./calibration/CalibrationScreen');
    return <CalibrationScreen kind={calibration} onExit={() => setCalibration(undefined)} />;
  }
  return <View style={styles.screen}>
    {selected ? <PlayerScreen key={`${selected.content_id}_${revision}`} item={selected} preferences={preferences}
      visible={!settings} onBack={() => setSelected(undefined)} onSettings={() => setSettings(true)}
      onRetry={() => setRevision(value => value + 1)} onCalibration={setCalibration} /> :
      settings ? null : !catalogReady || !settingsReady ? <View style={styles.loading}>
        <Text style={styles.title}>No Strobe-lem</Text><Text style={styles.body}>{error || 'Loading your viewing experience…'}</Text>
        {!!error && <FocusButton label="Retry catalog" preferred onPress={() => setAttempt(value => value + 1)} />}
        <FocusButton label="Settings" onPress={() => setSettings(true)} />
      </View> : <Catalog items={items} profile={preferences.profile} selectedId={selectedId}
        onSelect={item => {setSelectedId(item.content_id); setSelected(item);}} onSettings={() => setSettings(true)} />}
    {catalogReady && !items.length && !selected && !settings && <FocusButton label="Retry catalog" onPress={() => setAttempt(value => value + 1)} />}
    {settings && settingsReady && <View style={styles.overlay}><Settings items={items} preferences={preferences}
      message={message} onChange={changePreferences} onBack={() => setSettings(false)} /></View>}
  </View>;
}
const styles = StyleSheet.create({screen: {flex: 1, backgroundColor: '#0e1823'}, loading: {padding: 48},
  title: {color: '#fff', fontSize: 32}, body: {color: '#b4c4d3', fontSize: 22, marginVertical: 24},
  overlay: {...StyleSheet.absoluteFillObject, zIndex: 30, backgroundColor: '#0e1823'},
});
