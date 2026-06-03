import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

export default function StudentCalendarScreen() {
  const [calendarData, setCalendarData] = useState<any>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  useEffect(() => {
    loadCalendar();
  }, []);

  const loadCalendar = async () => {
    const studentId = await AsyncStorage.getItem('studentId');
    if (studentId) {
      try {
        const response = await axios.get(`${API_URL}/api/student/calendar/${studentId}`);
        setCalendarData(response.data);
      } catch (error) {
        console.error('Error:', error);
      }
    }
  };

  const getDaysInMonth = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstDay = new Date(year, month, 1).getDay();
    const days = [];
    
    // Empty cells for days before the first day of month
    for (let i = 0; i < (firstDay === 0 ? 6 : firstDay - 1); i++) {
      days.push(null);
    }
    
    // Days of the month
    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month, i);
      const dayOfWeek = date.getDay() === 0 ? 7 : date.getDay();
      const isClassDay = calendarData?.schedule_days?.includes(dayOfWeek);
      const isPast = date < today;
      days.push({
        day: i,
        date: date.toISOString().split('T')[0],
        isClassDay,
        isPast,
      });
    }
    
    return days;
  };

  const dayNames = ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya'];
  const monthNames = [
    'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun',
    'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr'
  ];
  const today = new Date();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>📅 Kalendar</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content}>
        <Text style={styles.monthTitle}>
          {monthNames[today.getMonth()]} {today.getFullYear()}
        </Text>

        <View style={styles.weekDays}>
          {dayNames.map((day, index) => (
            <Text key={index} style={styles.weekDay}>{day}</Text>
          ))}
        </View>

        <View style={styles.calendarGrid}>
          {getDaysInMonth().map((dayInfo: any, index) => (
            <TouchableOpacity
              key={index}
              style={styles.dayCell}
              onPress={() => dayInfo && dayInfo.isClassDay && setSelectedDate(dayInfo.date)}
              disabled={!dayInfo}
            >
              {dayInfo && (
                <>
                  <Text style={[
                    styles.dayText,
                    dayInfo.day === today.getDate() && styles.todayText
                  ]}>{dayInfo.day}</Text>
                  {dayInfo.isClassDay && (
                    <View style={[
                      styles.dot,
                      dayInfo.isPast && styles.dotPast
                    ]} />
                  )}
                </>
              )}
            </TouchableOpacity>
          ))}
        </View>

        {selectedDate && calendarData && (
          <View style={styles.detailsCard}>
            <Text style={styles.detailsTitle}>📖 Dars ma'lumotlari</Text>
            <Text style={styles.detailsText}>📅 Sana: {selectedDate}</Text>
            <Text style={styles.detailsText}>⏰ Vaqt: {calendarData.time}</Text>
            <Text style={styles.detailsText}>📚 Mavzu: {calendarData.subject}</Text>
            <Text style={styles.detailsText}>🏠 Xona: {calendarData.room}</Text>
            <Text style={styles.detailsText}>👨‍🏫 Ustoz: {calendarData.teacher_name}</Text>
          </View>
        )}

        <View style={styles.legend}>
          <Text style={styles.legendTitle}>Tushuntirish:</Text>
          <View style={styles.legendItem}>
            <View style={styles.dot} />
            <Text style={styles.legendText}>Dars kuni</Text>
          </View>
          <View style={styles.legendItem}>
            <View style={[styles.dot, styles.dotPast]} />
            <Text style={styles.legendText}>O'tgan dars</Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingBottom: 15,
    paddingHorizontal: 20,
    backgroundColor: '#e74c3c',
  },
  backText: { fontSize: 28, color: '#fff' },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#fff' },
  content: { flex: 1, padding: 20 },
  monthTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginBottom: 20,
  },
  weekDays: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 10,
  },
  weekDay: {
    width: '14%',
    textAlign: 'center',
    fontWeight: 'bold',
    color: '#666',
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 10,
    marginBottom: 20,
  },
  dayCell: {
    width: '14.28%',
    aspectRatio: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 5,
  },
  dayText: { fontSize: 16, color: '#333' },
  todayText: {
    fontWeight: 'bold',
    color: '#e74c3c',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3498db',
    marginTop: 2,
  },
  dotPast: { backgroundColor: '#2ecc71' },
  detailsCard: {
    backgroundColor: '#fff',
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
    elevation: 3,
  },
  detailsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  detailsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  legend: {
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  legendTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 5,
  },
  legendText: { marginLeft: 10, color: '#666' },
});
