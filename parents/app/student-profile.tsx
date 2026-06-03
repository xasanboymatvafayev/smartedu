import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentProfileScreen() {
  const [profile, setProfile] = useState<any>(null);

  useEffect(() => { loadProfile(); }, []);

  const loadProfile = async () => {
    const studentId = await AsyncStorage.getItem('studentId');
    if (studentId) {
      try {
        const response = await axios.get(`${API_URL}/api/student/profile/${studentId}`);
        setProfile(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  if (!profile) {
    return (
      <View style={styles.container}>
        <Text style={styles.loading}>Yuklanmoqda...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>👤 Profil</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content}>
        <LinearGradient colors={['#e74c3c', '#c0392b']} style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{profile.name?.[0]?.toUpperCase()}</Text>
          </View>
          <Text style={styles.profileName}>{profile.name}</Text>
          <Text style={styles.profilePhone}>📞 {profile.phone}</Text>
        </LinearGradient>

        <View style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>💰 Balans</Text>
          <Text style={styles.balanceValue}>{profile.balance?.toLocaleString()} so'm</Text>
        </View>

        <View style={styles.coinsCard}>
          <Text style={styles.balanceLabel}>🪙 Coinlar</Text>
          <Text style={styles.balanceValue}>{profile.coins}</Text>
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>📋 Ma'lumotlar</Text>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Telefon:</Text>
            <Text style={styles.infoValue}>{profile.phone}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Ota-ona telefoni:</Text>
            <Text style={styles.infoValue}>{profile.parent_phone}</Text>
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Holat:</Text>
            <Text style={[styles.infoValue, profile.status === 'frozen' && styles.frozenStatus]}>
              {profile.status === 'active' ? '✅ Faol' : '❄️ Muzlatilgan'}
            </Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, backgroundColor: '#e74c3c' },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  loading: { textAlign: 'center', marginTop: 100, fontSize: 18 },
  content: { flex: 1, padding: 20 },
  profileCard: { padding: 30, borderRadius: 15, alignItems: 'center', marginBottom: 20 },
  avatar: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#fff', justifyContent: 'center', alignItems: 'center', marginBottom: 15 },
  avatarText: { fontSize: 36, fontWeight: 'bold', color: '#e74c3c' },
  profileName: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 5 },
  profilePhone: { fontSize: 14, color: '#fff', opacity: 0.9 },
  balanceCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 15, elevation: 3 },
  coinsCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 15, elevation: 3 },
  balanceLabel: { fontSize: 14, color: '#666', marginBottom: 5 },
  balanceValue: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  infoCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 30, elevation: 3 },
  infoTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 15 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  infoLabel: { fontSize: 14, color: '#666' },
  infoValue: { fontSize: 14, color: '#333', fontWeight: '600' },
  frozenStatus: { color: '#3498db' },
});
