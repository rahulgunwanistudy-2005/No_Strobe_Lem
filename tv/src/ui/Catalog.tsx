import React from 'react';
import {Image, ScrollView, StyleSheet, Text, View} from 'react-native';
import {assetUrl} from '../catalog/api';
import type {CatalogItem} from '../catalog/api';
import type {Profile} from '../types/hazardtrack';
import {FocusButton} from './FocusButton';
import {formatTime} from './hazards';
export function Catalog({items, profile, selectedId, onSelect, onSettings}: {
  items: CatalogItem[]; profile: Profile; selectedId?: string;
  onSelect: (item: CatalogItem) => void; onSettings: () => void;
}) {
  return <View style={styles.page}>
    <Text style={styles.brand}>No Strobe-lem</Text>
    <View style={styles.heading}><Text style={styles.title}>Pick a title. Watch with a viewing aid.</Text>
      <FocusButton label={`Settings · ${profile}`} onPress={onSettings} preferred={!items.length} /></View>
    <Text style={styles.subtitle}>Flashing segments are softened with a timed veil. You can skip them, too.</Text>
    {!items.length && <Text style={styles.subtitle}>No titles yet. Add analyzed titles to the catalog and retry.</Text>}
    <ScrollView><View style={styles.grid}>{items.map((item, i) => {
      const info = item.tracks[profile];
      return <FocusButton key={item.content_id} label={item.title} onPress={() => onSelect(item)}
        preferred={selectedId ? selectedId === item.content_id : i === 0}>
        <View style={styles.card}>
          {item.poster ? <Image source={{uri: assetUrl(item.poster)}} style={styles.poster} /> :
            <View style={[styles.poster, styles.placeholder]}><Text style={styles.brand}>NS</Text></View>}
          <Text numberOfLines={2} style={styles.cardTitle}>{item.title}</Text>
          <Text style={styles.subtitle}>{formatTime(item.duration_s)} · {profile}</Text>
          <Text style={styles.badge}>{info ? `${info.hazard_count} flashing segments softened` : 'Not analyzed — no protection'}</Text>
          {!!item.description && <Text numberOfLines={2} style={styles.description}>{item.description}</Text>}
        </View>
      </FocusButton>;
    })}</View></ScrollView>
  </View>;
}
const styles = StyleSheet.create({
  page: {flex: 1, padding: 40, backgroundColor: '#0e1823'}, brand: {color: '#8cf0d1', fontSize: 25, fontWeight: '700'},
  heading: {flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between'},
  title: {color: '#fff', fontSize: 30, flex: 1}, subtitle: {color: '#b4c4d3', fontSize: 18, marginVertical: 6},
  grid: {flexDirection: 'row', flexWrap: 'wrap', paddingTop: 16}, card: {width: 330},
  poster: {width: 330, height: 110, borderRadius: 6}, placeholder: {backgroundColor: '#31475a', justifyContent: 'center', alignItems: 'center'},
  cardTitle: {fontSize: 24, color: '#fff', marginTop: 12}, badge: {color: '#8cf0d1', fontSize: 17, marginVertical: 8},
  description: {color: '#b4c4d3', fontSize: 15},
});
