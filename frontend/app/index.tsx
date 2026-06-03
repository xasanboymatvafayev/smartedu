import React, { useState, useEffect } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, Alert,
  KeyboardAvoidingView, Platform, ScrollView, Linking,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function LoginScreen() {
  const [step, setStep] = useState('role');
  const [role, setRole] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState('');
  const [hasPassword, setHasPassword] = useState(false);

  useEffect(() => { checkLogin(); }, []);

  const checkLogin = async () => {
    const userRole = await AsyncStorage.getItem('userRole');
    if (userRole === 'boss') {
      const centerId = await AsyncStorage.getItem('centerId');
      if (centerId) router.replace('/dashboard');
    } else if (userRole === 'teacher') {
      const teacherId = await AsyncStorage.getItem('teacherId');
      if (teacherId) router.replace('/teacher-dashboard');
    } else if (userRole === 'student' || userRole === 'parent') {
      const studentId = await AsyncStorage.getItem('studentId');
      if (studentId) router.replace('/student-dashboard');
    }
  };

  const selectRole = (selectedRole: string) => {
    setRole(selectedRole);
    setStep('login');
  };

  const handleLogin = async () => {
    if (!phone) { Alert.alert('Xato', 'Telefon raqamni kiriting'); return; }
    setLoading(true);

    try {
      if (role === 'boss') {
        if (!password) { Alert.alert('Xato', 'Parolni kiriting'); setLoading(false); return; }
        const response = await axios.post(`${API_URL}/api/boss/login`, { phone, password });
        if (response.data.success) {
          await AsyncStorage.setItem('userRole', 'boss');
          await AsyncStorage.setItem('centerId', response.data.center_id);
          await AsyncStorage.setItem('centerName', response.data.center_name);
          await AsyncStorage.setItem('tariff', response.data.tariff);
          router.replace('/dashboard');
        }
      } else if (role === 'teacher') {
        if (password) {
          try {
            const response = await axios.post(`${API_URL}/api/teacher/login`, { phone, password });
            if (response.data.success) {
              await AsyncStorage.setItem('userRole', 'teacher');
              await AsyncStorage.setItem('teacherId', response.data.teacher_id);
              await AsyncStorage.setItem('teacherName', response.data.name);
              router.replace('/teacher-dashboard');
              setLoading(false);
              return;
            }
          } catch (err) {
            // Continue to verification
          }
        }
        await axios.post(`${API_URL}/api/teacher/request-code`, { phone });
        Alert.alert(
          'Telegram Kod',
          "Telegram botimizga o'ting va tasdiqlash kodini oling:\nhttps://t.me/SmartEduVerificationBot",
          [{ text: 'OK' }]
        );
        setStep('verify');
      } else if (role === 'student' || role === 'parent') {
        if (password) {
          try {
            const response = await axios.post(`${API_URL}/api/student/login`, { phone, password, user_type: role });
            if (response.data.success) {
              await AsyncStorage.setItem('userRole', role);
              await AsyncStorage.setItem('studentId', response.data.student_id);
              await AsyncStorage.setItem('studentName', response.data.name);
              router.replace('/student-dashboard');
              setLoading(false);
              return;
            }
          } catch (err) {
            // Continue to verification
          }
        }
        await axios.post(`${API_URL}/api/student/request-code`, { phone, user_type: role });
        Alert.alert(
          'Telegram Kod',
          "Telegram botimizga o'ting va tasdiqlash kodini oling:\nhttps://t.me/SmartEduVerificationBot",
          [{ text: 'OK' }]
        );
        setStep('verify');
      }
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
      if (role === 'teacher') {
        const response = await axios.post(`${API_URL}/api/teacher/verify-code`, { phone, code });
        setUserId(response.data.teacher_id);
        setHasPassword(response.data.has_password);
        if (response.data.has_password) {
          Alert.alert('Muvaffaqiyat', 'Parolingiz bilan kiring');
          setStep('login');
        } else {
          setStep('setPassword');
        }
      } else {
        const response = await axios.post(`${API_URL}/api/student/verify-code`, { phone, code, user_type: role });
        setUserId(response.data.student_id);
        setHasPassword(response.data.has_password);
        if (response.data.has_password) {
          Alert.alert('Muvaffaqiyat', 'Parolingiz bilan kiring');
          setStep('login');
        } else {
          setStep('setPassword');
        }
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
      if (role === 'teacher') {
        await axios.post(`${API_URL}/api/teacher/set-password`, { teacher_id: userId, password: newPassword });
        const loginRes = await axios.post(`${API_URL}/api/teacher/login`, { phone, password: newPassword });
        await AsyncStorage.setItem('userRole', 'teacher');
        await AsyncStorage.setItem('teacherId', loginRes.data.teacher_id);
        await AsyncStorage.setItem('teacherName', loginRes.data.name);
        router.replace('/teacher-dashboard');
      } else {
        await axios.post(`${API_URL}/api/student/set-password`, { student_id: userId, password: newPassword });
        const loginRes = await axios.post(`${API_URL}/api/student/login`, { phone, password: newPassword, user_type: role });
        await AsyncStorage.setItem('userRole', role);
        await AsyncStorage.setItem('studentId', loginRes.data.student_id);
        await AsyncStorage.setItem('studentName', loginRes.data.name);
        router.replace('/student-dashboard');
      }
    } catch (error: any) {
      Alert.alert('Xato', error.response?.data?.detail || 'Xatolik yuz berdi');
    } finally {
      setLoading(false);
    }
  };

  const openTelegramBot = () => {
    Linking.openURL('https://t.me/SmartEduVerificationBot');
  };

  if (step === 'role') {
    return (
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.container}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.bigTitle}>🎓 EDU TIZIM</Text>
          <Text style={styles.bigSubtitle}>O'zingizni tanlang</Text>

          <TouchableOpacity style={[styles.roleCard, styles.bossCard]} onPress={() => selectRole('boss')}>
            <Text style={styles.roleIcon}>👔</Text>
            <Text style={styles.roleTitle}>O'quv Markaz Admin</Text>
            <Text style={styles.roleSubtitle}>Boss / Direktor</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.roleCard, styles.teacherCard]} onPress={() => selectRole('teacher')}>
            <Text style={styles.roleIcon}>👨‍🏫</Text>
            <Text style={styles.roleTitle}>Ustoz</Text>
            <Text style={styles.roleSubtitle}>O'qituvchi</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.roleCard, styles.studentCard]} onPress={() => selectRole('student')}>
            <Text style={styles.roleIcon}>🎓</Text>
            <Text style={styles.roleTitle}>O'quvchi</Text>
            <Text style={styles.roleSubtitle}>Talaba</Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.roleCard, styles.parentCard]} onPress={() => selectRole('parent')}>
            <Text style={styles.roleIcon}>👪</Text>
            <Text style={styles.roleTitle}>Ota-Ona</Text>
            <Text style={styles.roleSubtitle}>Farzand uchun</Text>
          </TouchableOpacity>
        </ScrollView>
      </LinearGradient>
    );
  }

  if (step === 'verify') {
    return (
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
        <LinearGradient colors={['#667eea', '#764ba2']} style={styles.gradient}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Text style={styles.title}>📱 Tasdiqlash</Text>
            <Text style={styles.subtitle}>Telegram botdan kod oling</Text>
            <View style={styles.formContainer}>
              <TouchableOpacity style={styles.telegramButton} onPress={openTelegramBot}>
                <Text style={styles.telegramButtonText}>🤖 Telegram Botga O'tish</Text>
              </TouchableOpacity>
              <TextInput
                style={styles.input}
                placeholder="6 raqamli kod"
                value={code}
                onChangeText={setCode}
                keyboardType="numeric"
                maxLength={6}
              />
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
        <LinearGradient colors={['#667eea', '#764ba2']} style={styles.gradient}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Text style={styles.title}>🔐 Yangi Parol</Text>
            <Text style={styles.subtitle}>Yangi parol o'ylab toping</Text>
            <View style={styles.formContainer}>
              <TextInput
                style={styles.input}
                placeholder="Yangi parol"
                value={newPassword}
                onChangeText={setNewPassword}
                secureTextEntry
              />
              <TouchableOpacity style={styles.loginButton} onPress={handleSetPassword} disabled={loading}>
                <Text style={styles.loginButtonText}>{loading ? 'Saqlanmoqda...' : 'Saqlash va Kirish'}</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </LinearGradient>
      </KeyboardAvoidingView>
    );
  }

  const roleLabel = role === 'boss' ? "O'quv Markaz" : role === 'teacher' ? 'Ustoz' : role === 'student' ? "O'quvchi" : 'Ota-Ona';

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <LinearGradient colors={['#667eea', '#764ba2']} style={styles.gradient}>
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.title}>🔐 Kirish</Text>
          <Text style={styles.subtitle}>{roleLabel}</Text>
          <View style={styles.formContainer}>
            <TextInput
              style={styles.input}
              placeholder="Telefon raqam"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
            />
            <TextInput
              style={styles.input}
              placeholder="Parol (agar bor bo'lsa)"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />
            <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={loading}>
              <Text style={styles.loginButtonText}>
                {loading ? 'Yuklanmoqda...' : role === 'boss' ? 'Kirish' : 'Kirish / Kod yuborish'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.backLink} onPress={() => setStep('role')}>
              <Text style={styles.backLinkText}>← Role o'zgartirish</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  scrollContent: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  bigTitle: { fontSize: 36, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 10 },
  bigSubtitle: { fontSize: 18, color: '#fff', textAlign: 'center', marginBottom: 40, opacity: 0.9 },
  title: { fontSize: 28, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 10 },
  subtitle: { fontSize: 16, color: '#fff', textAlign: 'center', marginBottom: 30, opacity: 0.9 },
  formContainer: { backgroundColor: '#fff', borderRadius: 20, padding: 25 },
  input: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 15, fontSize: 16, marginBottom: 15, borderWidth: 1, borderColor: '#ddd' },
  loginButton: { backgroundColor: '#667eea', borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 10 },
  loginButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  backLink: { alignItems: 'center', marginTop: 15 },
  backLinkText: { color: '#667eea', fontSize: 14 },
  roleCard: { backgroundColor: '#fff', padding: 25, borderRadius: 15, marginBottom: 15, alignItems: 'center' },
  bossCard: { borderLeftWidth: 5, borderLeftColor: '#667eea' },
  teacherCard: { borderLeftWidth: 5, borderLeftColor: '#2ecc71' },
  studentCard: { borderLeftWidth: 5, borderLeftColor: '#e74c3c' },
  parentCard: { borderLeftWidth: 5, borderLeftColor: '#f39c12' },
  roleIcon: { fontSize: 50, marginBottom: 10 },
  roleTitle: { fontSize: 20, fontWeight: 'bold', color: '#333', marginBottom: 5 },
  roleSubtitle: { fontSize: 14, color: '#666' },
  telegramButton: { backgroundColor: '#0088cc', padding: 15, borderRadius: 10, alignItems: 'center', marginBottom: 15 },
  telegramButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
});
