# EDU TIZIM - PRD

## Loyiha haqida
O'quv markazlar uchun to'liq boshqaruv tizimi: web admin panel + 3 ta mobile app (Boss, Teacher, Student/Parent).

## Implementatsiya qilingan funksiyalar

### Web Admin Panel
- 2-bosqichli login
- Dashboard statistika
- O'quv markazlar CRUD
- Tarif boshqaruvi (Pro 200k, Pro+ 500k, VIP)
- Muzlatish/Faollashtirish

### Mobile App - Boss
- Login, Dashboard
- Xonalar, Guruhlar, Ustozlar, Kurslar, O'quvchilar
- Do'kon (mahsulot + buyurtmalar)
- Balans to'ldirish

### Mobile App - Teacher
- Telegram verification login
- Bugungi darslar, Barcha guruhlar
- O'quvchilar ko'rish
- Coin qo'shish
- Davomat belgilash

### Mobile App - Student/Parent
- Role tanlash (Student/Parent)
- Telegram verification login
- Dashboard (balans, coinlar)
- Kalendar (yashil/ko'k nuqtalar)
- Reyting (guruh + markaz)
- Do'kon (coinlar bilan)
- Profil

### Backend
- FastAPI + MongoDB
- bcrypt password hashing
- Telegram Bot integration
- Avtomatik balans yechish (dars kunlari)
- Coin tizimi

## Tech Stack
- Backend: FastAPI, MongoDB, python-telegram-bot
- Frontend: Expo 54, React Native, axios, expo-router
- Auth: bcrypt + Telegram verification codes

## Test Credentials
Admin: 998901234567 / admin123 / admin456
Boss: 998901111111 / boss123
Teacher: 998902222222 / teacher123
Student: 998903333333 / student123
Parent: 998904444444 / student123
