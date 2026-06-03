import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentDashboard() {
  const [studentName, setStudentName] = useState('');
  const [stats, setStats] = useState({ balance: 0, coins: 0, group_name: '', attendance_count: 0 });

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    const studentId = await AsyncStorage.getItem('studentId');
    const name = await AsyncStorage.getItem('studentName');
    setStudentName(name || '');

    if (studentId) {
      try {
        const response = await axios.get(`${API_URL}/api/student/dashboard/${studentId}`);
        setStats(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const handleLogout = async () => {
    await AsyncStorage.clear();
    router.replace('/');
  };

  const menuItems = [
    { title: 'Kalendar', icon: '📅', route: '/student-calendar' },
    { title: 'Reyting', icon: '🏆', route: '/student-ranking' },
    { title: "Do'kon", icon: '🛒', route: '/student-store' },
    { title: 'Profil', icon: '👤', route: '/student-profile' },
  ];

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#e74c3c', '#c0392b']} style={styles.header}>
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>🎓 {studentName}</Text>
            <Text style={styles.headerSubtitle}>O'quvchi Paneli</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
            <Text style={styles.logoutText}>🚪</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content}>
        <Text style={styles.sectionTitle}>📊 Mening Statistikam</Text>
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.balance.toLocaleString()}</Text>
            <Text style={styles.statLabel}>Balans (so'm)</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.coins}</Text>
            <Text style={styles.statLabel}>Coinlar</Text>
          </View>
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoText}>📚 Guruh: {stats.group_name}</Text>
          <Text style={styles.infoText}>✅ Qatnashgan darslar: {stats.attendance_count}</Text>
        </View>

        <Text style={styles.sectionTitle}>🎯 Bo'limlar</Text>
        <View style={styles.menuGrid}>
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={styles.menuItem}
              onPress={() => router.push(item.route as any)}
            >
              <Text style={styles.menuIcon}>{item.icon}</Text>
              <Text style={styles.menuTitle}>{item.title}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { paddingTop: 50, paddingBottom: 20, paddingHorizontal: 20 },
  headerContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { fontSize: 24, fontWeight: 'bold', color: '#fff' },
  headerSubtitle: { fontSize: 14, color: '#fff', opacity: 0.9, marginTop: 5 },
  logoutButton: { padding: 10 },
  logoutText: { fontSize: 24 },
  content: { flex: 1, padding: 20 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 15, marginTop: 10 },
  statsContainer: { flexDirection: 'row', gap: 10, marginBottom: 20 },
  statCard: { flex: 1, backgroundColor: '#fff', padding: 20, borderRadius: 15, alignItems: 'center', elevation: 3 },
  statValue: { fontSize: 24, fontWeight: 'bold', color: '#e74c3c', marginBottom: 5 },
  statLabel: { fontSize: 14, color: '#666' },
  infoCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 20, elevation: 3 },
  infoText: { fontSize: 16, color: '#333', marginBottom: 8 },
  menuGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 15, marginBottom: 30 },
  menuItem: { width: '47%', backgroundColor: '#fff', padding: 25, borderRadius: 15, alignItems: 'center', elevation: 3 },
  menuIcon: { fontSize: 40, marginBottom: 10 },
  menuTitle: { fontSize: 16, fontWeight: '600', color: '#333', textAlign: 'center' },
});
