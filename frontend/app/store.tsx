import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Modal, Alert, Image } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StoreScreen() {
  const [items, setItems] = useState([]);
  const [orders, setOrders] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [ordersModalVisible, setOrdersModalVisible] = useState(false);
  const [formData, setFormData] = useState({ name: '', coin_price: '', image_base64: '' });
  const [centerId, setCenterId] = useState('');

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    const id = await AsyncStorage.getItem('centerId');
    setCenterId(id || '');
    if (id) {
      const [itemsRes, ordersRes] = await Promise.all([
        axios.get(`${API_URL}/api/boss/store/${id}`),
        axios.get(`${API_URL}/api/boss/store/orders/${id}`),
      ]);
      setItems(itemsRes.data);
      setOrders(ordersRes.data);
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.5,
      base64: true,
    });

    if (!result.canceled && result.assets[0].base64) {
      setFormData({...formData, image_base64: `data:image/jpeg;base64,${result.assets[0].base64}`});
    }
  };

  const handleCreate = async () => {
    if (!formData.name || !formData.coin_price || !formData.image_base64) {
      Alert.alert('Xato', 'Barcha maydonlarni to\'ldiring');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/boss/store`, { center_id: centerId, ...formData, coin_price: parseInt(formData.coin_price) });
      setModalVisible(false);
      setFormData({ name: '', coin_price: '', image_base64: '' });
      loadData();
      Alert.alert('Muvaffaqiyat', 'Mahsulot qo\'shildi');
    } catch (error) {
      Alert.alert('Xato', 'Mahsulot qo\'shishda xatolik');
    }
  };

  const completeOrder = async (orderId: string) => {
    await axios.put(`${API_URL}/api/boss/store/orders/${orderId}/complete`, {});
    loadData();
    Alert.alert('Muvaffaqiyat', 'Buyurtma bajarildi');
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>🛒 Do'kon</Text>
        <TouchableOpacity onPress={() => setModalVisible(true)} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.ordersButton} onPress={() => setOrdersModalVisible(true)}>
        <Text style={styles.ordersButtonText}>📦 Buyurtmalar ({orders.filter((o: any) => o.status === 'pending').length})</Text>
      </TouchableOpacity>

      <ScrollView style={styles.content}>
        {items.map((item: any) => (
          <View key={item.id} style={styles.itemCard}>
            {item.image_base64 && <Image source={{ uri: item.image_base64 }} style={styles.itemImage} />}
            <View style={styles.itemInfo}>
              <Text style={styles.itemName}>{item.name}</Text>
              <Text style={styles.itemPrice}>🪙 {item.coin_price} coin</Text>
            </View>
          </View>
        ))}
      </ScrollView>

      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Yangi Mahsulot</Text>
            <TouchableOpacity style={styles.imagePickerButton} onPress={pickImage}>
              {formData.image_base64 ? <Image source={{ uri: formData.image_base64 }} style={styles.previewImage} /> : <Text>🖼️ Rasm tanlash</Text>}
            </TouchableOpacity>
            <TextInput style={styles.input} placeholder="Mahsulot nomi" value={formData.name} onChangeText={(v) => setFormData({...formData, name: v})} />
            <TextInput style={styles.input} placeholder="Coin narxi" value={formData.coin_price} onChangeText={(v) => setFormData({...formData, coin_price: v})} keyboardType="numeric" />
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={() => setModalVisible(false)}><Text>Bekor</Text></TouchableOpacity>
              <TouchableOpacity style={styles.submitButton} onPress={handleCreate}><Text style={styles.submitButtonText}>Qo'shish</Text></TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      <Modal visible={ordersModalVisible} transparent animationType="slide">
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>📦 Buyurtmalar</Text>
            <ScrollView style={styles.ordersList}>
              {orders.filter((o: any) => o.status === 'pending').map((order: any) => (
                <View key={order.id} style={styles.orderCard}>
                  <Text style={styles.orderText}>👤 {order.student_name}</Text>
                  <Text style={styles.orderText}>📦 {order.item_name}</Text>
                  <Text style={styles.orderText}>🪙 {order.coin_price} coin</Text>
                  <TouchableOpacity style={styles.completeButton} onPress={() => completeOrder(order.id)}>
                    <Text style={styles.completeButtonText}>✅ Bajarish</Text>
                  </TouchableOpacity>
                </View>
              ))}
            </ScrollView>
            <TouchableOpacity style={styles.closeButton} onPress={() => setOrdersModalVisible(false)}><Text>Yopish</Text></TouchableOpacity>
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
  ordersButton: { margin: 20, padding: 15, backgroundColor: '#f39c12', borderRadius: 10, alignItems: 'center' },
  ordersButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  itemCard: { flexDirection: 'row', backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 10, elevation: 3 },
  itemImage: { width: 60, height: 60, borderRadius: 8, marginRight: 15 },
  itemInfo: { flex: 1, justifyContent: 'center' },
  itemName: { fontSize: 16, fontWeight: 'bold', color: '#333', marginBottom: 5 },
  itemPrice: { fontSize: 14, color: '#667eea' },
  modalContainer: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { backgroundColor: '#fff', borderRadius: 20, padding: 25, width: '85%', maxHeight: '80%' },
  modalTitle: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 20 },
  imagePickerButton: { height: 150, backgroundColor: '#f5f5f5', borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: 15, borderWidth: 1, borderColor: '#ddd' },
  previewImage: { width: '100%', height: '100%', borderRadius: 10 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 15, marginBottom: 15, borderWidth: 1, borderColor: '#ddd' },
  modalButtons: { flexDirection: 'row', gap: 10, marginTop: 10 },
  cancelButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#f5f5f5' },
  submitButton: { flex: 1, padding: 15, borderRadius: 10, alignItems: 'center', backgroundColor: '#667eea' },
  submitButtonText: { color: '#fff', fontWeight: 'bold' },
  ordersList: { maxHeight: 400, marginBottom: 15 },
  orderCard: { backgroundColor: '#f5f5f5', padding: 15, borderRadius: 10, marginBottom: 10 },
  orderText: { fontSize: 14, color: '#333', marginBottom: 5 },
  completeButton: { marginTop: 10, padding: 10, backgroundColor: '#2ecc71', borderRadius: 8, alignItems: 'center' },
  completeButtonText: { color: '#fff', fontWeight: 'bold' },
  closeButton: { padding: 15, backgroundColor: '#f5f5f5', borderRadius: 10, alignItems: 'center' },
});
