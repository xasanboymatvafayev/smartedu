import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function TeacherGroupScreen() {
  const { groupId } = useLocalSearchParams();
  const [students, setStudents] = useState([]);
  const [group, setGroup] = useState<any>(null);

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/teacher/group/${groupId}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const awardCoin = async (studentId: string, studentName: string) => {
    Alert.prompt(
      'Coin Berish',
      `${studentName} ga nechta coin berasiz?`,
      [
        { text: 'Bekor', style: 'cancel' },
        {
          text: 'Berish',
          onPress: async (coins) => {
            if (coins && parseInt(coins) > 0) {
              try {
                await axios.post(`${API_URL}/api/teacher/award-coin`, {
                  student_id: studentId,
                  coins: parseInt(coins),
                });
                Alert.alert('Muvaffaqiyat', `${coins} coin berildi`);
                loadStudents();
              } catch (error) {
                Alert.alert('Xato', 'Coin berishda xatolik');
              }
            }
          },
        },
      ],
      'plain-text',
      '5'
    );
  };

  const markAttendance = async (studentId: string, studentName: string, status: number) => {
    const today = new Date().toISOString().split('T')[0];
    try {
      await axios.post(`${API_URL}/api/teacher/attendance`, {
        group_id: groupId,
        student_id: studentId,
        status: status,
        date: today,
      });
      Alert.alert(
        'Muvaffaqiyat',
        status === 1 ? `${studentName} darsda` : `${studentName} darsda yo'q`
      );
    } catch (error) {
      Alert.alert('Xato', 'Davomat belgilashda xatolik');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>👥 O'quvchilar</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content}>
        {students.map((student: any) => (
          <View key={student.id} style={styles.studentCard}>
            <View style={styles.studentHeader}>
              <Text style={styles.studentName}>{student.name}</Text>
              <Text style={styles.studentCoins}>🪙 {student.coins}</Text>
            </View>
            <Text style={styles.studentPhone}>📞 {student.phone}</Text>
            
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.actionButton, styles.presentButton]}
                onPress={() => markAttendance(student.id, student.name, 1)}
              >
                <Text style={styles.actionButtonText}>✅ Keldi</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.absentButton]}
                onPress={() => markAttendance(student.id, student.name, 0)}
              >
                <Text style={styles.actionButtonText}>❌ Kelmadi</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionButton, styles.coinButton]}
                onPress={() => awardCoin(student.id, student.name)}
              >
                <Text style={styles.actionButtonText}>🪙 Coin</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 20,
    backgroundColor: '#2ecc71',
  },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  content: { flex: 1, padding: 20 },
  studentCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginBottom: 15,
    elevation: 3,
  },
  studentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  studentName: { fontSize: 18, fontWeight: 'bold', color: '#333' },
  studentCoins: { fontSize: 16, fontWeight: 'bold', color: '#f39c12' },
  studentPhone: { fontSize: 14, color: '#666', marginBottom: 15 },
  actionButtons: { flexDirection: 'row', gap: 8 },
  actionButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  presentButton: { backgroundColor: '#2ecc71' },
  absentButton: { backgroundColor: '#e74c3c' },
  coinButton: { backgroundColor: '#f39c12' },
  actionButtonText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
});
