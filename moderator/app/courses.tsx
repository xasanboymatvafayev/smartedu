import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Modal,
  Alert,
  RefreshControl,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function CoursesScreen() {
  const [courses, setCourses] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [courseName, setCourseName] = useState('');
  const [monthlyFee, setMonthlyFee] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [centerId, setCenterId] = useState('');

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      try {
        const response = await axios.get(`${API_URL}/api/boss/courses/${id}`);
        setCourses(response.data);
      } catch (error) {
        console.error('Error loading courses:', error);
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCourses();
    setRefreshing(false);
  };

  const handleCreateCourse = async () => {
    if (!courseName.trim() || !monthlyFee) {
      Alert.alert('Xato', 'Barcha maydonlarni to\'ldiring');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/boss/courses`, {
        center_id: centerId,
        name: courseName,
        monthly_fee: parseFloat(monthlyFee),
      });
      setModalVisible(false);
      setCourseName('');
      setMonthlyFee('');
      loadCourses();
      Alert.alert('Muvaffaqiyat', 'Kurs yaratildi');
    } catch (error) {
      Alert.alert('Xato', 'Kurs yaratishda xatolik');
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>📚 Kurslar</Text>
        <TouchableOpacity
          onPress={() => setModalVisible(true)}
          style={styles.addButton}
        >
          <Text style={styles.addButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {courses.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Hozircha kurslar yo'q</Text>
          </View>
        ) : (
          courses.map((course: any) => (
            <View key={course.id} style={styles.courseCard}>
              <View style={styles.courseInfo}>
                <Text style={styles.courseName}>{course.name}</Text>
                <Text style={styles.courseFee}>
                  💰 {course.monthly_fee.toLocaleString()} so'm/oy
                </Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi Kurs</Text>
            <TextInput
              style={styles.input}
              placeholder="Kurs nomi (masalan: Ingliz tili)"
              value={courseName}
              onChangeText={setCourseName}
            />
            <TextInput
              style={styles.input}
              placeholder="Oylik to'lov (so'm)"
              value={monthlyFee}
              onChangeText={setMonthlyFee}
              keyboardType="numeric"
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setModalVisible(false);
                  setCourseName('');
                  setMonthlyFee('');
                }}
              >
                <Text style={styles.cancelButtonText}>Bekor qilish</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.submitButton]}
                onPress={handleCreateCourse}
              >
                <Text style={styles.submitButtonText}>Yaratish</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 20,
    backgroundColor: '#667eea',
  },
  backButton: {
    padding: 10,
  },
  backText: {
    fontSize: 28,
    color: '#fff',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    fontSize: 24,
    color: '#667eea',
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  emptyState: {
    marginTop: 100,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
  },
  courseCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  courseInfo: {
    flex: 1,
  },
  courseName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  courseFee: {
    fontSize: 16,
    color: '#667eea',
    fontWeight: '600',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 25,
    width: '85%',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 10,
  },
  modalButton: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#667eea',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
