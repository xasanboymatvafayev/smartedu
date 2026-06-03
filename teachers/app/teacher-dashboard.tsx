import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function TeacherDashboard() {
  const [teacherName, setTeacherName] = useState('');
  const [stats, setStats] = useState({ total_groups: 0, today_classes: 0, groups: [] });
  const [allGroups, setAllGroups] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { loadDashboard(); }, []);

  const loadDashboard = async () => {
    const teacherId = await AsyncStorage.getItem('teacherId');
    const name = await AsyncStorage.getItem('teacherName');
    setTeacherName(name || '');

    if (teacherId) {
      try {
        const [dashboardRes, groupsRes] = await Promise.all([
          axios.get(`${API_URL}/api/teacher/dashboard/${teacherId}`),
          axios.get(`${API_URL}/api/teacher/groups/${teacherId}`),
        ]);
        setStats(dashboardRes.data);
        setAllGroups(groupsRes.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadDashboard();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await AsyncStorage.clear();
    router.replace('/');
  };

  const dayNames = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh'];

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#2ecc71', '#27ae60']} style={styles.header}>
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>👨‍🏫 {teacherName}</Text>
            <Text style={styles.headerSubtitle}>Ustoz Paneli</Text>
          </View>
          <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
            <Text style={styles.logoutText}>🚪</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <ScrollView style={styles.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.total_groups}</Text>
            <Text style={styles.statLabel}>Jami guruhlar</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{stats.today_classes}</Text>
            <Text style={styles.statLabel}>Bugungi darslar</Text>
          </View>
        </View>

        {stats.today_classes > 0 && (
          <>
            <Text style={styles.sectionTitle}>📅 Bugungi Darslar</Text>
            {stats.groups.map((group: any) => (
              <TouchableOpacity
                key={group.id}
                style={[styles.groupCard, styles.todayCard]}
                onPress={() => router.push(`/teacher-group?groupId=${group.id}` as any)}
              >
                <View style={styles.todayBadge}>
                  <Text style={styles.todayBadgeText}>BUGUN</Text>
                </View>
                <Text style={styles.groupName}>{group.name}</Text>
                <Text style={styles.groupDetail}>⏰ {group.time_start} - {group.time_end}</Text>
                <Text style={styles.groupDetail}>📖 {group.subject}</Text>
                <Text style={styles.groupDetail}>🏠 {group.room}</Text>
              </TouchableOpacity>
            ))}
          </>
        )}

        <Text style={styles.sectionTitle}>📚 Barcha Guruhlar</Text>
        {allGroups.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Hozircha guruhlar yo'q</Text>
          </View>
        ) : (
          allGroups.map((group: any) => (
            <TouchableOpacity
              key={group.id}
              style={styles.groupCard}
              onPress={() => router.push(`/teacher-group?groupId=${group.id}` as any)}
            >
              <Text style={styles.groupName}>{group.name}</Text>
              <Text style={styles.groupDetail}>📖 {group.subject}</Text>
              <Text style={styles.groupDetail}>⏰ {group.time_start} - {group.time_end}</Text>
              <Text style={styles.groupDetail}>🏠 {group.room}</Text>
              <View style={styles.daysRow}>
                {[1, 2, 3, 4, 5, 6].map((day) => (
                  <View key={day} style={[styles.dayBadge, group.schedule_days?.includes(day) && styles.dayBadgeActive]}>
                    <Text style={[styles.dayBadgeText, group.schedule_days?.includes(day) && styles.dayBadgeTextActive]}>
                      {dayNames[day - 1]}
                    </Text>
                  </View>
                ))}
              </View>
              <Text style={styles.studentsCount}>👥 {group.students_count} o'quvchi</Text>
            </TouchableOpacity>
          ))
        )}
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
  statsRow: { flexDirection: 'row', gap: 15, marginBottom: 20 },
  statCard: { flex: 1, backgroundColor: '#fff', padding: 20, borderRadius: 15, alignItems: 'center', elevation: 3 },
  statValue: { fontSize: 32, fontWeight: 'bold', color: '#2ecc71', marginBottom: 5 },
  statLabel: { fontSize: 14, color: '#666' },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 15, marginTop: 10 },
  emptyState: { padding: 40, alignItems: 'center' },
  emptyText: { fontSize: 16, color: '#666' },
  groupCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 10, elevation: 3 },
  todayCard: { borderLeftWidth: 5, borderLeftColor: '#f39c12' },
  todayBadge: { position: 'absolute', top: 10, right: 10, backgroundColor: '#f39c12', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 5 },
  todayBadgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
  groupName: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  groupDetail: { fontSize: 14, color: '#666', marginBottom: 4 },
  daysRow: { flexDirection: 'row', gap: 5, marginVertical: 10 },
  dayBadge: { width: 30, height: 30, borderRadius: 15, backgroundColor: '#f5f5f5', justifyContent: 'center', alignItems: 'center' },
  dayBadgeActive: { backgroundColor: '#2ecc71' },
  dayBadgeText: { fontSize: 12, color: '#999' },
  dayBadgeTextActive: { color: '#fff', fontWeight: 'bold' },
  studentsCount: { fontSize: 14, color: '#666', marginTop: 5 },
});
