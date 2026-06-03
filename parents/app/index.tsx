import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert,
  KeyboardAvoidingView, Platform, ScrollView, Image, Linking,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const ROLE = 'parent';

export default function LoginScreen() {
  const [step, setStep] = useState('login'); // login, verify, setPassword
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState('');
  const [testCode, setTestCode] = useState('');

  useEffect(() => { checkLogin(); }, []);

  const checkLogin = async () => {
    const userRole = await AsyncStorage.getItem('userRole');
    if (userRole === 'parent') {
      const studentId = await AsyncStorage.getItem('studentId');
      if (studentId) router.replace('/student-dashboard');
    }
  };

  const handleLogin = async () => {
    if (!phone) { Alert.alert('Xato', 'Telefon raqamni kiriting'); return; }
    setLoading(true);
    try {
      if (password) {
        try {
          const response = await axios.post(`${API_URL}/api/student/login`, { phone, password, user_type: ROLE });
          if (response.data.success) {
            await AsyncStorage.setItem('userRole', ROLE);
            await AsyncStorage.setItem('studentId', response.data.student_id);
            await AsyncStorage.setItem('studentName', response.data.name);
            router.replace('/student-dashboard');
            setLoading(false);
            return;
          }
        } catch (err) { /* Continue to verification */ }
      }
      const response = await axios.post(`${API_URL}/api/student/request-code`, { phone, user_type: ROLE });
      setTestCode(response.data.code);
      Alert.alert(
        'Telegram Kod',
        `Bot orqali kod oling: https://t.me/SmartEduVerificationBot\n\nTest uchun: ${response.data.code}`,
        [{ text: 'OK' }]
      );
      setStep('verify');
    } catch (error: any) {
      Alert.alert('Xato', error.response?.data?.detail || 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!code) { Alert.alert('Xato', 'Kodni kiriting'); return; }
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/student/verify-code`, { phone, code, user_type: ROLE });
      setUserId(response.data.student_id);
      if (response.data.has_password) {
        Alert.alert('Muvaffaqiyat', 'Parolingiz bilan kiring');
        setStep('login');
      } else {
        setStep('setPassword');
      }
    } catch (error: any) {
      Alert.alert('Xato', error.response?.data?.detail || "Kod noto'g'ri");
    } finally {
      setLoading(false);
    }
  };

  const handleSetPassword = async () => {
    if (!newPassword || newPassword.length < 4) {
      Alert.alert('Xato', "Parol kamida 4 ta belgi bo'lishi kerak");
      return;
    }
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/student/set-password`, { student_id: userId, password: newPassword });
      const loginRes = await axios.post(`${API_URL}/api/student/login`, { phone, password: newPassword, user_type: ROLE });
      await AsyncStorage.setItem('userRole', ROLE);
      await AsyncStorage.setItem('studentId', loginRes.data.student_id);
      await AsyncStorage.setItem('studentName', loginRes.data.name);
      router.replace('/student-dashboard');
    } catch (error: any) {
      Alert.alert('Xato', error.response?.data?.detail || 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'verify') {
    return (
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
        <LinearGradient colors={['#7b1a1a', '#c0392b']} style={styles.gradient}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Image source={require('../assets/images/icon.png')} style={styles.logo} resizeMode="contain" />
            <Text style={styles.title}>📱 Tasdiqlash</Text>
            <Text style={styles.subtitle}>Telegram botdan kod oling</Text>
            <View style={styles.formContainer}>
              <TouchableOpacity style={styles.telegramButton} onPress={() => Linking.openURL('https://t.me/SmartEduVerificationBot')}>
                <Text style={styles.telegramButtonText}>🤖 SmartEduVerificationBot</Text>
              </TouchableOpacity>
              <Text style={styles.testCodeText}>Test kod: {testCode}</Text>
              <TextInput style={styles.input} placeholder="6 raqamli kod" value={code} onChangeText={setCode} keyboardType="numeric" maxLength={6} />
              <TouchableOpacity style={styles.loginButton} onPress={handleVerifyCode} disabled={loading}>
                <Text style={styles.loginButtonText}>{loading ? 'Tekshirilmoqda...' : 'Tasdiqlash'}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.backLink} onPress={() => setStep('login')}>
                <Text style={styles.backLinkText}>← Orqaga</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </LinearGradient>
      </KeyboardAvoidingView>
    );
  }

  if (step === 'setPassword') {
    return (
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
        <LinearGradient colors={['#7b1a1a', '#c0392b']} style={styles.gradient}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Image source={require('../assets/images/icon.png')} style={styles.logo} resizeMode="contain" />
            <Text style={styles.title}>🔐 Yangi Parol</Text>
            <Text style={styles.subtitle}>Yangi parol yarating</Text>
            <View style={styles.formContainer}>
              <TextInput style={styles.input} placeholder="Yangi parol" value={newPassword} onChangeText={setNewPassword} secureTextEntry />
              <TouchableOpacity style={styles.loginButton} onPress={handleSetPassword} disabled={loading}>
                <Text style={styles.loginButtonText}>{loading ? 'Saqlanmoqda...' : 'Saqlash va Kirish'}</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </LinearGradient>
      </KeyboardAvoidingView>
    );
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <LinearGradient colors={['#7b1a1a', '#c0392b']} style={styles.gradient}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Image source={require('../assets/images/icon.png')} style={styles.logo} resizeMode="contain" />
          <Text style={styles.title}>SmartEdu Parents</Text>
          <Text style={styles.subtitle}>Ota-onalar uchun panel</Text>
          <View style={styles.formContainer}>
            <Text style={styles.label}>📱 Telefon raqam</Text>
            <TextInput style={styles.input} placeholder="+998 xx xxx xx xx" value={phone} onChangeText={setPhone} keyboardType="phone-pad" placeholderTextColor="#aaa" />
            <Text style={styles.label}>🔐 Parol (agar bor bo'lsa)</Text>
            <TextInput style={styles.input} placeholder="Parolingizni kiriting" value={password} onChangeText={setPassword} secureTextEntry placeholderTextColor="#aaa" />
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={loading}>
              <Text style={styles.loginButtonText}>{loading ? 'Yuklanmoqda...' : '🚀 Kirish / Kod yuborish'}</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.versionText}>SmartEdu v1.0 • Parents</Text>
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
  subtitle: { fontSize: 14, color: '#fcc', textAlign: 'center', marginBottom: 32, opacity: 0.85 },
  formContainer: { backgroundColor: '#fff', borderRadius: 20, padding: 24, shadowColor: '#000', shadowOpacity: 0.15, shadowRadius: 12, elevation: 8 },
  label: { fontSize: 14, fontWeight: '600', color: '#444', marginBottom: 6 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 14, fontSize: 16, marginBottom: 16, borderWidth: 1, borderColor: '#e0e0e0', color: '#333' },
  loginButton: { backgroundColor: '#7b1a1a', borderRadius: 12, padding: 16, alignItems: 'center', marginTop: 8 },
  loginButtonText: { color: '#fff', fontSize: 17, fontWeight: 'bold' },
  telegramButton: { backgroundColor: '#0088cc', padding: 14, borderRadius: 10, alignItems: 'center', marginBottom: 14 },
  telegramButtonText: { color: '#fff', fontSize: 15, fontWeight: 'bold' },
  testCodeText: { textAlign: 'center', color: '#999', fontSize: 13, marginBottom: 14 },
  backLink: { alignItems: 'center', marginTop: 14 },
  backLinkText: { color: '#7b1a1a', fontSize: 14 },
  versionText: { textAlign: 'center', color: 'rgba(255,255,255,0.5)', fontSize: 12, marginTop: 24 },
});
