import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Modal, Alert, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function GroupsScreen() {
  const [groups, setGroups] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    subject: '',
    room: '',
    time_start: '',
    time_end: '',
    schedule_days: [] as number[],
  });
  const [refreshing, setRefreshing] = useState(false);
  const [centerId, setCenterId] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      try {
        const [groupsRes, roomsRes, teachersRes] = await Promise.all([
          axios.get(`${API_URL}/api/boss/groups/${id}`),
          axios.get(`${API_URL}/api/boss/rooms/${id}`),
          axios.get(`${API_URL}/api/boss/teachers/${id}`),
        ]);
        setGroups(groupsRes.data);
        setRooms(roomsRes.data);
        setTeachers(teachersRes.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const toggleDay = (day: number) => {
    const days = formData.schedule_days.includes(day)
      ? formData.schedule_days.filter(d => d !== day)
      : [...formData.schedule_days, day];
    setFormData({ ...formData, schedule_days: days });
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.subject || !formData.room || !formData.time_start || !formData.time_end || formData.schedule_days.length === 0) {
      Alert.alert('Xato', 'Barcha maydonlarni to\'ldiring');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/boss/groups`, {
        center_id: centerId,
        ...formData,
      });
      setModalVisible(false);
      setFormData({ name: '', subject: '', room: '', time_start: '', time_end: '', schedule_days: [] });
      loadData();
      Alert.alert('Muvaffaqiyat', 'Guruh yaratildi');
    } catch (error) {
      Alert.alert('Xato', 'Guruh yaratishda xatolik');
    }
  };

  const dayNames = ['Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan'];

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>👥 Guruhlar</Text>
        <TouchableOpacity onPress={() => setModalVisible(true)} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
      </View>

      <ScrollView style={styles.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={loadData} />}>
        {groups.map((group: any) => (
          <View key={group.id} style={styles.groupCard}>
            <Text style={styles.groupName}>{group.name}</Text>
            <Text style={styles.groupDetail}>📖 {group.subject}</Text>
            <Text style={styles.groupDetail}>🏠 {group.room} | ⏰ {group.time_start}-{group.time_end}</Text>
            <Text style={styles.groupDetail}>👨‍🏫 {group.teacher_name || 'Ustoz biriktirilmagan'}</Text>
            <Text style={styles.groupDetail}>👥 {group.students_count} o'quvchi</Text>
          </View>
        ))}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi Guruh</Text>
            <TextInput style={styles.input} placeholder="Guruh nomi" value={formData.name} onChangeText={(v) => setFormData({...formData, name: v})} />
            <TextInput style={styles.input} placeholder="Fan nomi" value={formData.subject} onChangeText={(v) => setFormData({...formData, subject: v})} />
            
            <Text style={styles.label}>Xona:</Text>
            <ScrollView horizontal style={styles.optionsScroll}>
              {rooms.map((room: any) => (
                <TouchableOpacity key={room.id} onPress={() => setFormData({...formData, room: room.name})} style={[styles.optionButton, formData.room === room.name && styles.optionButtonActive]}>
                  <Text style={formData.room === room.name ? styles.optionTextActive : styles.optionText}>{room.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <TextInput style={styles.input} placeholder="Boshlanish vaqti (14:00)" value={formData.time_start} onChangeText={(v) => setFormData({...formData, time_start: v})} />
            <TextInput style={styles.input} placeholder="Tugash vaqti (16:00)" value={formData.time_end} onChangeText={(v) => setFormData({...formData, time_end: v})} />
            
            <Text style={styles.label}>Dars kunlari:</Text>
            <View style={styles.daysContainer}>
              {[1, 2, 3, 4, 5, 6].map((day) => (
                <TouchableOpacity key={day} onPress={() => toggleDay(day)} style={[styles.dayButton, formData.schedule_days.includes(day) && styles.dayButtonActive]}>
                  <Text style={formData.schedule_days.includes(day) ? styles.dayTextActive : styles.dayText}>{dayNames[day-1]}</Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setModalVisible(false)}><Text>Bekor</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreate}><Text style={styles.submitButtonText}>Yaratish</Text></TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, backgroundColor: '#667eea' },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  addButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#fff', justifyContent: 'center', alignItems: 'center' },
  addButtonText: { fontSize: 24, color: '#667eea', fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  groupCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 10, elevation: 3 },
  groupName: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  groupDetail: { fontSize: 14, color: '#666', marginBottom: 4 },
  modalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', padding: 20 },
  modalContent: { backgroundColor: '#fff', borderRadius: 20, padding: 25, width: '100%', maxHeight: '90%' },
  modalTitle: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 15, marginBottom: 15, borderWidth: 1, borderColor: '#ddd' },
  label: { fontSize: 16, fontWeight: '600', marginBottom: 10 },
  optionsScroll: { flexDirection: 'row', marginBottom: 15 },
  optionButton: { padding: 10, marginRight: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ddd' },
  optionButtonActive: { backgroundColor: '#667eea', borderColor: '#667eea' },
  optionText: { color: '#333' },
  optionTextActive: { color: '#fff' },
  daysContainer: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 15, gap: 8 },
  dayButton: { padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ddd' },
  dayButtonActive: { backgroundColor: '#667eea', borderColor: '#667eea' },
  dayText: { color: '#333' },
  dayTextActive: { color: '#fff' },
  modalButtons: { flexDirection: 'row', gap: 10, marginTop: 10 },
  cancelButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#f5f5f5' },
  submitButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#667eea' },
  submitButtonText: { color: '#fff', fontWeight: 'bold' },
});
