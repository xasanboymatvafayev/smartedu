import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert,
  KeyboardAvoidingView, Platform, ScrollView, Image,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function LoginScreen() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => { checkLogin(); }, []);

  const checkLogin = async () => {
    const userRole = await AsyncStorage.getItem('userRole');
    if (userRole === 'boss') {
      const centerId = await AsyncStorage.getItem('centerId');
      if (centerId) router.replace('/dashboard');
    }
  };

  const handleLogin = async () => {
    if (!phone) { Alert.alert('Xato', 'Telefon raqamni kiriting'); return; }
    if (!password) { Alert.alert('Xato', 'Parolni kiriting'); return; }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/boss/login`, { phone, password });
      if (response.data.success) {
        await AsyncStorage.setItem('userRole', 'boss');
        await AsyncStorage.setItem('centerId', response.data.center_id);
        await AsyncStorage.setItem('centerName', response.data.center_name);
        await AsyncStorage.setItem('tariff', response.data.tariff);
        router.replace('/dashboard');
      }
    } catch (error: any) {
      Alert.alert('Xato', error.response?.data?.detail || 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <LinearGradient colors={['#2c3e7a', '#1a5276']} style={styles.gradient}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Image
            source={require('../assets/images/icon.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.title}>SmartEdu Moderator</Text>
          <Text style={styles.subtitle}>O'quv markaz boshqaruv paneli</Text>

          <View style={styles.formContainer}>
            <Text style={styles.label}>📱 Telefon raqam</Text>
            <TextInput
              style={styles.input}
              placeholder="+998 xx xxx xx xx"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              placeholderTextColor="#aaa"
            />

            <Text style={styles.label}>🔐 Parol</Text>
            <TextInput
              style={styles.input}
              placeholder="Parolingizni kiriting"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholderTextColor="#aaa"
            />

            <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={loading}>
              <Text style={styles.loginButtonText}>
                {loading ? 'Yuklanmoqda...' : '🚀 Kirish'}
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.versionText}>SmartEdu v1.0 • Moderator Panel</Text>
        </ScrollView>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  scrollContent: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  logo: { width: 120, height: 120, alignSelf: 'center', marginBottom: 16, borderRadius: 24 },
  title: { fontSize: 26, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 6 },
  subtitle: { fontSize: 14, color: '#cce', textAlign: 'center', marginBottom: 32, opacity: 0.85 },
  formContainer: { backgroundColor: '#fff', borderRadius: 20, padding: 24, shadowColor: '#000', shadowOpacity: 0.15, shadowRadius: 12, elevation: 8 },
  label: { fontSize: 14, fontWeight: '600', color: '#444', marginBottom: 6 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 14, fontSize: 16, marginBottom: 16, borderWidth: 1, borderColor: '#e0e0e0', color: '#333' },
  loginButton: { backgroundColor: '#2c3e7a', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 8 },
  loginButtonText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  versionText: { textAlign: 'center', color: 'rgba(255,255,255,0.5)', fontSize: 12, marginTop: 24 },
});
