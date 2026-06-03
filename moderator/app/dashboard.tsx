import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function DashboardScreen() {
  const [centerName, setCenterName] = useState('');
  const [stats, setStats] = useState({
    students_count: 0,
    groups_count: 0,
    teachers_count: 0,
    monthly_revenue: 0,
  });
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    const centerId = await AsyncStorage.getItem('centerId');
    const name = await AsyncStorage.getItem('centerName');
    setCenterName(name || '');

    if (centerId) {
      try {
        const response = await axios.get(
          `${API_URL}/api/boss/dashboard/${centerId}`
        );
        setStats(response.data);
      } catch (error) {
        console.error('Error loading dashboard:', error);
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboard();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    Alert.alert('Chiqish', 'Rostdan ham chiqmoqchimisiz?', [
      { text: 'Yo\'q', style: 'cancel' },
      {
        text: 'Ha',
        onPress: async () => {
          await AsyncStorage.clear();
          router.replace('/');
        },
      },
    ]);
  };

  const menuItems = [
    { title: 'Xonalar', icon: '🏠', route: '/rooms' },
    { title: 'Guruhlar', icon: '👥', route: '/groups' },
    { title: 'Ustozlar', icon: '👨‍🏫', route: '/teachers' },
    { title: 'Kurslar', icon: '📚', route: '/courses' },
    { title: 'O\'quvchilar', icon: '🎓', route: '/students' },
    { title: 'Do\'kon', icon: '🛒', route: '/store' },
  ];

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.header}>
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>{centerName}</Text>
            <Text style={styles.headerSubtitle}>O'quv Markaz Boshqaruvi</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
            <Text style={styles.logoutText}>🚪</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <Text style={styles.sectionTitle}>📊 Statistika</Text>
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.students_count}</Text>
            <Text style={styles.statLabel}>O'quvchilar</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.groups_count}</Text>
            <Text style={styles.statLabel}>Guruhlar</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.teachers_count}</Text>
            <Text style={styles.statLabel}>Ustozlar</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              {Math.round(stats.monthly_revenue).toLocaleString()}
            </Text>
            <Text style={styles.statLabel}>Balans (so'm)</Text>
          </View>
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
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
    marginTop: 5,
  },
  logoutButton: {
    padding: 10,
  },
  logoutText: {
    fontSize: 24,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    marginTop: 10,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 20,
    gap: 10,
  },
  statCard: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#667eea',
    marginBottom: 5,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 15,
    marginBottom: 30,
  },
  menuItem: {
    width: '47%',
    backgroundColor: '#fff',
    padding: 25,
    borderRadius: 15,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  menuIcon: {
    fontSize: 40,
    marginBottom: 10,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    textAlign: 'center',
  },
});