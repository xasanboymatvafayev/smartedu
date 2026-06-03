import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentRankingScreen() {
  const [data, setData] = useState<any>({ group_ranking: [], center_ranking: [], my_coins: 0 });
  const [activeTab, setActiveTab] = useState<'group' | 'center'>('group');

  useEffect(() => { loadRanking(); }, []);

  const loadRanking = async () => {
    const studentId = await AsyncStorage.getItem('studentId');
    if (studentId) {
      try {
        const response = await axios.get(`${API_URL}/api/student/ranking/${studentId}`);
        setData(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const ranking = activeTab === 'group' ? data.group_ranking : data.center_ranking;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>🏆 Reyting</Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={styles.myCoinsCard}>
        <Text style={styles.myCoinsLabel}>Mening Coinlarim</Text>
        <Text style={styles.myCoinsValue}>🪙 {data.my_coins}</Text>
      </View>

      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'group' && styles.tabActive]}
          onPress={() => setActiveTab('group')}
        >
          <Text style={activeTab === 'group' ? styles.tabTextActive : styles.tabText}>Guruh</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'center' && styles.tabActive]}
          onPress={() => setActiveTab('center')}
        >
          <Text style={activeTab === 'center' ? styles.tabTextActive : styles.tabText}>O'quv Markaz</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {ranking.map((student: any, index: number) => (
          <View key={index} style={styles.rankCard}>
            <View style={[styles.rankNumber, index === 0 && styles.rankGold, index === 1 && styles.rankSilver, index === 2 && styles.rankBronze]}>
              <Text style={styles.rankText}>{index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}</Text>
            </View>
            <Text style={styles.rankName}>{student.name}</Text>
            <Text style={styles.rankCoins}>🪙 {student.coins}</Text>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, backgroundColor: '#e74c3c' },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  myCoinsCard: { backgroundColor: '#f39c12', margin: 20, padding: 20, borderRadius: 15, alignItems: 'center' },
  myCoinsLabel: { color: '#fff', fontSize: 14, marginBottom: 5 },
  myCoinsValue: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  tabs: { flexDirection: 'row', marginHorizontal: 20, marginBottom: 10, backgroundColor: '#fff', borderRadius: 10, padding: 5 },
  tab: { flex: 1, padding: 12, alignItems: 'center', borderRadius: 8 },
  tabActive: { backgroundColor: '#e74c3c' },
  tabText: { color: '#666', fontWeight: '600' },
  tabTextActive: { color: '#fff', fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  rankCard: { flexDirection: 'row', backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 10, alignItems: 'center' },
  rankNumber: { width: 50, height: 50, borderRadius: 25, backgroundColor: '#f5f5f5', justifyContent: 'center', alignItems: 'center', marginRight: 15 },
  rankGold: { backgroundColor: '#FFD700' },
  rankSilver: { backgroundColor: '#C0C0C0' },
  rankBronze: { backgroundColor: '#CD7F32' },
  rankText: { fontSize: 16, fontWeight: 'bold' },
  rankName: { flex: 1, fontSize: 16, fontWeight: '600', color: '#333' },
  rankCoins: { fontSize: 16, fontWeight: 'bold', color: '#f39c12' },
});
