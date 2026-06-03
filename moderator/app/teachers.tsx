import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Modal, Alert, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function TeachersScreen() {
  const [teachers, setTeachers] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [formData, setFormData] = useState({ name: '', phone: '', password: '' });
  const [centerId, setCenterId] = useState('');

  useEffect(() => { loadTeachers(); }, []);

  const loadTeachers = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      const res = await axios.get(`${API_URL}/api/boss/teachers/${id}`);
      setTeachers(res.data);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.phone || !formData.password) {
      Alert.alert('Xato', 'Barcha maydonlarni to\'ldiring');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/boss/teachers`, { center_id: centerId, ...formData, groups: [] });
      setModalVisible(false);
      setFormData({ name: '', phone: '', password: '' });
      loadTeachers();
      Alert.alert('Muvaffaqiyat', 'Ustoz qo\'shildi');
    } catch (error) {
      Alert.alert('Xato', 'Ustoz qo\'shishda xatolik');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>👨‍🏫 Ustozlar</Text>
        <TouchableOpacity onPress={() => setModalVisible(true)} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {teachers.map((teacher: any) => (
          <View key={teacher.id} style={styles.teacherCard}>
            <Text style={styles.teacherName}>{teacher.name}</Text>
            <Text style={styles.teacherDetail}>📞 {teacher.phone}</Text>
            <Text style={styles.teacherDetail}>📚 {teacher.groups.length} guruh</Text>
          </View>
        ))}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi Ustoz</Text>
            <TextInput style={styles.input} placeholder="Ism familiya" value={formData.name} onChangeText={(v) => setFormData({...formData, name: v})} />
            <TextInput style={styles.input} placeholder="Telefon" value={formData.phone} onChangeText={(v) => setFormData({...formData, phone: v})} keyboardType="phone-pad" />
            <TextInput style={styles.input} placeholder="Parol" value={formData.password} onChangeText={(v) => setFormData({...formData, password: v})} secureTextEntry />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setModalVisible(false)}><Text>Bekor</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreate}><Text style={styles.submitButtonText}>Qo'shish</Text></TouchableOpacity>
            </View>
          </View>
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
  teacherCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 10, elevation: 3 },
  teacherName: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  teacherDetail: { fontSize: 14, color: '#666', marginBottom: 4 },
  modalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { backgroundColor: '#fff', borderRadius: 20, padding: 25, width: '85%' },
  modalTitle: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 15, marginBottom: 15, borderWidth: 1, borderColor: '#ddd' },
  modalButtons: { flexDirection: 'row', gap: 10, marginTop: 10 },
  cancelButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#f5f5f5' },
  submitButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#667eea' },
  submitButtonText: { color: '#fff', fontWeight: 'bold' },
});
