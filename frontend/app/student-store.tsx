import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Image, Alert } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentStoreScreen() {
  const [items, setItems] = useState([]);
  const [myCoins, setMyCoins] = useState(0);

  useEffect(() => { loadStore(); }, []);

  const loadStore = async () => {
    const studentId = await AsyncStorage.getItem('studentId');
    if (studentId) {
      try {
        const [profileRes] = await Promise.all([
          axios.get(`${API_URL}/api/student/profile/${studentId}`),
        ]);
        const centerId = profileRes.data.center_id;
        setMyCoins(profileRes.data.coins || 0);
        
        const itemsRes = await axios.get(`${API_URL}/api/student/store/${centerId}`);
        setItems(itemsRes.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const orderItem = (item: any) => {
    if (myCoins < item.coin_price) {
      Alert.alert('Yetarli emas', 'Sizda yetarli coin yo\'q');
      return;
    }

    Alert.alert(
      'Buyurtma',
      `${item.name} ni ${item.coin_price} coin uchun buyurtma berasizmi?`,
      [
        { text: 'Yo\'q', style: 'cancel' },
        {
          text: 'Ha',
          onPress: async () => {
            try {
              const studentId = await AsyncStorage.getItem('studentId');
              await axios.post(`${API_URL}/api/student/store/order`, {
                student_id: studentId,
                item_id: item.id,
              });
              Alert.alert('Muvaffaqiyat', 'Buyurtma berildi! Ustozdan oling.');
              loadStore();
            } catch (error: any) {
              Alert.alert('Xato', error.response?.data?.detail || 'Buyurtma berishda xatolik');
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={styles.backText}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>🛒 Do'kon</Text>
        <View style={styles.coinsBadge}>
          <Text style={styles.coinsText}>🪙 {myCoins}</Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
        {items.length === 0 ? (
          <Text style={styles.emptyText}>Hozircha mahsulotlar yo'q</Text>
        ) : (
          items.map((item: any) => (
            <View key={item.id} style={styles.itemCard}>
              {item.image_base64 && <Image source={{ uri: item.image_base64 }} style={styles.itemImage} />}
              <View style={styles.itemInfo}>
                <Text style={styles.itemName}>{item.name}</Text>
                <Text style={styles.itemPrice}>🪙 {item.coin_price} coin</Text>
                <TouchableOpacity
                  style={[styles.buyButton, myCoins < item.coin_price && styles.buyButtonDisabled]}
                  onPress={() => orderItem(item)}
                  disabled={myCoins < item.coin_price}
                >
                  <Text style={styles.buyButtonText}>
                    {myCoins >= item.coin_price ? 'Sotib olish' : 'Yetarli emas'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, backgroundColor: '#e74c3c' },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  coinsBadge: { backgroundColor: '#f39c12', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 15 },
  coinsText: { color: '#fff', fontWeight: 'bold' },
  content: { flex: 1, padding: 20 },
  emptyText: { textAlign: 'center', color: '#666', marginTop: 50 },
  itemCard: { flexDirection: 'row', backgroundColor: '#fff', padding: 15, borderRadius: 10, marginBottom: 15, elevation: 3 },
  itemImage: { width: 80, height: 80, borderRadius: 8, marginRight: 15 },
  itemInfo: { flex: 1, justifyContent: 'center' },
  itemName: { fontSize: 16, fontWeight: 'bold', color: '#333', marginBottom: 5 },
  itemPrice: { fontSize: 14, color: '#f39c12', marginBottom: 10 },
  buyButton: { backgroundColor: '#2ecc71', padding: 10, borderRadius: 8, alignItems: 'center' },
  buyButtonDisabled: { backgroundColor: '#ccc' },
  buyButtonText: { color: '#fff', fontWeight: 'bold' },
});
