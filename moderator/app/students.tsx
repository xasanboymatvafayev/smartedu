import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Modal, Alert, RefreshControl } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentsScreen() {
  const [students, setStudents] = useState([]);
  const [groups, setGroups] = useState([]);
  const [courses, setCourses] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [balanceModal, setBalanceModal] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [balanceAmount, setBalanceAmount] = useState('');
  const [formData, setFormData] = useState({ name: '', phone: '', parent_phone: '', group_id: '', course_id: '', password: '' });
  const [centerId, setCenterId] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      const [studentsRes, groupsRes, coursesRes] = await Promise.all([
        axios.get(`${API_URL}/api/boss/students/${id}`),
        axios.get(`${API_URL}/api/boss/groups/${id}`),
        axios.get(`${API_URL}/api/boss/courses/${id}`),
      ]);
      setStudents(studentsRes.data);
      setGroups(groupsRes.data);
      setCourses(coursesRes.data);
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.phone || !formData.parent_phone || !formData.group_id || !formData.course_id || !formData.password) {
      Alert.alert('Xato', 'Barcha maydonlarni to\'ldiring');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/boss/students`, { center_id: centerId, ...formData, balance: 0, coins: 0, status: 'active' });
      setModalVisible(false);
      setFormData({ name: '', phone: '', parent_phone: '', group_id: '', course_id: '', password: '' });
      loadData();
      Alert.alert('Muvaffaqiyat', 'O\'quvchi qo\'shildi');
    } catch (error) {
      Alert.alert('Xato', 'O\'quvchi qo\'shishda xatolik');
    }
  };

  const handleTopup = async () => {
    if (!balanceAmount || !selectedStudent) return;
    try {
      await axios.put(`${API_URL}/api/boss/students/${selectedStudent.id}/balance`, { amount: parseFloat(balanceAmount) });
      setBalanceModal(false);
      setBalanceAmount('');
      setSelectedStudent(null);
      loadData();
      Alert.alert('Muvaffaqiyat', 'Balans to\'ldirildi');
    } catch (error) {
      Alert.alert('Xato', 'Balans to\'ldirishda xatolik');
    }
  };

  const toggleStatus = async (studentId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'frozen' : 'active';
    await axios.put(`${API_URL}/api/boss/students/${studentId}/status`, { status: newStatus });
    loadData();
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>🎓 O'quvchilar</Text>
        <TouchableOpacity onPress={() => setModalVisible(true)} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {students.map((student: any) => (
          <View key={student.id} style={styles.studentCard}>
            <Text style={styles.studentName}>{student.name} {student.status === 'frozen' && '❄️'}</Text>
            <Text style={styles.studentDetail}>📞 {student.phone} | 👪 {student.parent_phone}</Text>
            <Text style={styles.studentDetail}>📚 {student.group_name} | 💼 {student.course_name}</Text>
            <Text style={styles.studentDetail}>💰 {student.balance.toLocaleString()} so'm | 🪙 {student.coins} coin</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity style={styles.smallButton} onPress={() => { setSelectedStudent(student); setBalanceModal(true); }}><Text>💵 To'ldirish</Text></TouchableOpacity>
              <TouchableOpacity style={styles.smallButton} onPress={() => toggleStatus(student.id, student.status)}><Text>{student.status === 'active' ? '❄️ Muzlatish' : '✅ Faollashtirish'}</Text></TouchableOpacity>
            </View>
          </View>
        ))}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <ScrollView style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi O'quvchi</Text>
            <TextInput style={styles.input} placeholder="Ism familiya" value={formData.name} onChangeText={(v) => setFormData({...formData, name: v})} />
            <TextInput style={styles.input} placeholder="Telefon" value={formData.phone} onChangeText={(v) => setFormData({...formData, phone: v})} keyboardType="phone-pad" />
            <TextInput style={styles.input} placeholder="Ota-ona telefoni" value={formData.parent_phone} onChangeText={(v) => setFormData({...formData, parent_phone: v})} keyboardType="phone-pad" />
            <TextInput style={styles.input} placeholder="Parol" value={formData.password} onChangeText={(v) => setFormData({...formData, password: v})} secureTextEntry />
            
            <Text style={styles.label}>Guruh:</Text>
            <ScrollView horizontal style={styles.optionsScroll}>
              {groups.map((group: any) => (
                <TouchableOpacity key={group.id} onPress={() => setFormData({...formData, group_id: group.id})} style={[styles.optionButton, formData.group_id === group.id && styles.optionButtonActive]}>
                  <Text style={formData.group_id === group.id ? styles.optionTextActive : styles.optionText}>{group.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <Text style={styles.label}>Kurs:</Text>
            <ScrollView horizontal style={styles.optionsScroll}>
              {courses.map((course: any) => (
                <TouchableOpacity key={course.id} onPress={() => setFormData({...formData, course_id: course.id})} style={[styles.optionButton, formData.course_id === course.id && styles.optionButtonActive]}>
                  <Text style={formData.course_id === course.id ? styles.optionTextActive : styles.optionText}>{course.name}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setModalVisible(false)}><Text>Bekor</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreate}><Text style={styles.submitButtonText}>Qo'shish</Text></TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </Modal>

      <Modal visible={balanceModal} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Balans To'ldirish</Text>
            <Text style={styles.studentNameModal}>{selectedStudent?.name}</Text>
            <TextInput style={styles.input} placeholder="Summa (so'm)" value={balanceAmount} onChangeText={setBalanceAmount} keyboardType="numeric" />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => { setBalanceModal(false); setBalanceAmount(''); }}><Text>Bekor</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleTopup}><Text style={styles.submitButtonText}>To'ldirish</Text></TouchableOpacity>
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
  studentCard: { backgroundColor: '#fff', padding: 20, borderRadius: 10, marginBottom: 10, elevation: 3 },
  studentName: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 8 },
  studentDetail: { fontSize: 14, color: '#666', marginBottom: 4 },
  studentNameModal: { fontSize: 16, color: '#333', marginBottom: 15, textAlign: 'center' },
  buttonRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  smallButton: { flex: 1, padding: 10, backgroundColor: '#f0f0f0', borderRadius: 8, alignItems: 'center' },
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
  modalButtons: { flexDirection: 'row', gap: 10, marginTop: 10 },
  cancelButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#f5f5f5' },
  submitButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#667eea' },
  submitButtonText: { color: '#fff', fontWeight: 'bold' },
});
