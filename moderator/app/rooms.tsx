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

export default function RoomsScreen() {
  const [rooms, setRooms] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [centerId, setCenterId] = useState('');

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      try {
        const response = await axios.get(`${API_URL}/api/boss/rooms/${id}`);
        setRooms(response.data);
      } catch (error) {
        console.error('Error loading rooms:', error);
      }
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRooms();
    setRefreshing(false);
  };

  const handleCreateRoom = async () => {
    if (!roomName.trim()) {
      Alert.alert('Xato', 'Xona nomini kiriting');
      return;
    }

    try {
      await axios.post(`${API_URL}/api/boss/rooms`, {
        center_id: centerId,
        name: roomName,
      });
      setModalVisible(false);
      setRoomName('');
      loadRooms();
      Alert.alert('Muvaffaqiyat', 'Xona yaratildi');
    } catch (error) {
      Alert.alert('Xato', 'Xona yaratishda xatolik');
    }
  };

  const handleDeleteRoom = (roomId: string, roomName: string) => {
    Alert.alert('O\'chirish', `${roomName} xonasini o'chirmoqchimisiz?`, [
      { text: 'Yo\'q', style: 'cancel' },
      {
        text: 'Ha',
        onPress: async () => {
          try {
            await axios.delete(`${API_URL}/api/boss/rooms/${roomId}`);
            loadRooms();
            Alert.alert('Muvaffaqiyat', 'Xona o\'chirildi');
          } catch (error) {
            Alert.alert('Xato', 'Xona o\'chirishda xatolik');
          }
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>🏠 Xonalar</Text>
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
        {rooms.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Hozircha xonalar yo'q</Text>
            <Text style={styles.emptySubtext}>+ tugmasini bosib xona qo'shing</Text>
          </View>
        ) : (
          rooms.map((room: any) => (
            <View key={room.id} style={styles.roomCard}>
              <View style={styles.roomInfo}>
                <Text style={styles.roomName}>{room.name}</Text>
              </View>
              <TouchableOpacity
                onPress={() => handleDeleteRoom(room.id, room.name)}
                style={styles.deleteButton}
              >
                <Text style={styles.deleteButtonText}>🗑️</Text>
              </TouchableOpacity>
            </View>
          ))
        )}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi Xona</Text>
            <TextInput
              style={styles.input}
              placeholder="Xona nomi (masalan: C1)"
              value={roomName}
              onChangeText={setRoomName}
            />
            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setModalVisible(false);
                  setRoomName('');
                }}
              >
                <Text style={styles.cancelButtonText}>Bekor qilish</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.submitButton]}
                onPress={handleCreateRoom}
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
    marginBottom: 5,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
  },
  roomCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginBottom: 10,
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  roomInfo: {
    flex: 1,
  },
  roomName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  deleteButton: {
    padding: 10,
  },
  deleteButtonText: {
    fontSize: 24,
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
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
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