# 🎓 EDU TIZIM - To'liq Loyiha

## ✅ TAYYOR FUNKSIYALAR

### 1. 🌐 KATTA ADMIN PANEL (Web)
- ✅ 2-bosqichli login (telefon + 2 parol)
- ✅ Dashboard (statistika)
- ✅ O'quv markazlar yaratish (Pro/Pro+/VIP tariflar)
- ✅ Tarif boshqaruvi
- ✅ Muzlatish/Faollashtirish
- ✅ O'chirish

**Login:** http://your-backend-url/api/admin-panel  
**Credentials:**
- Phone: `998901234567`
- Parol 1: `admin123`
- Parol 2: `admin456`

### 2. 📱 EDU BOSS (Mobile)
- ✅ Login (telefon + parol)
- ✅ Dashboard (statistika)
- ✅ Xonalar (yaratish, o'chirish)
- ✅ Guruhlar (yaratish, ustoz biriktirish, dars kunlari)
- ✅ Ustozlar (yaratish, parol, telefon)
- ✅ Kurslar (oylik to'lov bilan)
- ✅ O'quvchilar (yaratish, balans to'ldirish, muzlatish)
- ✅ Do'kon (mahsulot qo'shish, buyurtmalar)

**Test Login:**
- Phone: `998901111111`
- Password: `boss123`

### 3. 👨‍🏫 EDU TEACHER (Mobile)
- ✅ Login (Telegram verification + parol)
- ✅ Dashboard (bugungi darslar, jami guruhlar)
- ✅ Barcha guruhlar ro'yxati
- ✅ Guruh ichida o'quvchilar ko'rish
- ✅ Coin qo'shish
- ✅ Davomat belgilash (1/0)
- ✅ Avtomatik balans yechish (1 dars = balansdan)

**Test Login:**
- Phone: `998902222222`
- Password: `teacher123`

### 4. 🎓 EDU STUDENT/PARENT (Mobile)
- ✅ Role tanlash (O'quvchi/Ota-Ona)
- ✅ Telegram verification login
- ✅ Dashboard (balans, coinlar, statistika)
- ✅ Kalendar (dars kunlari yashil/ko'k nuqtalar)
- ✅ Kun bosib dars malumotlarini ko'rish
- ✅ Reyting (guruh + markaz)
- ✅ Do'kon (coinlar bilan sotib olish)
- ✅ Profil

**Test Login:**
- Student Phone: `998903333333`
- Parent Phone: `998904444444`
- Password: `student123`

### 5. 🤖 TELEGRAM BOT INTEGRATION
- ✅ Verification code yuborish
- ✅ Bot webhook (/start command)
- ✅ Phone number linking
- Bot Token: `8922878571:AAHMRa1Atm4cawMYaJG73joIkdO_QoWDXyo`

---

## 🚀 DEPLOY QILISH

### A. Railway Deploy (Backend)

```bash
# 1. Railway CLI o'rnatish
npm install -g @railway/cli

# 2. Login qilish
railway login

# 3. Project yaratish
cd /app/backend
railway init

# 4. MongoDB qo'shish
railway add  # MongoDB tanlang

# 5. Environment variables
railway variables set MONGO_URL="${{MongoDB.MONGO_URL}}"
railway variables set DB_NAME="edu_tizim"

# 6. Deploy
railway up

# 7. Domain olish
railway domain
```

### B. Telegram Bot Webhook Setup

Backend deploy bo'lgach, webhook'ni sozlang:

```bash
# Replace YOUR_RAILWAY_URL bilan haqiqiy URL
curl "https://YOUR_RAILWAY_URL/api/telegram/setup?url=https://YOUR_RAILWAY_URL"
```

---

## 📱 APK YARATISH

### Usul 1: Emergent Publish (TAVSIYA)
1. Emergent platformada **"Publish"** tugmasini bosing (yuqori o'ng burchak)
2. Android APK tanlang
3. App name: `Edu Tizim`
4. Build tugagach yuklab oling

### Usul 2: EAS Build (Qo'lda)

```bash
# 1. EAS CLI
npm install -g eas-cli

# 2. Expo account
eas login

# 3. Configure
cd /app/frontend
eas build:configure

# 4. APK build
eas build --platform android --profile preview

# 5. Yuklab olish (link email orqali keladi)
```

### app.json Sozlamasi

```json
{
  "expo": {
    "name": "Edu Tizim",
    "slug": "edu-tizim",
    "version": "1.0.0",
    "android": {
      "package": "com.edutizim.app",
      "versionCode": 1,
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE",
        "INTERNET"
      ]
    },
    "ios": {
      "bundleIdentifier": "com.edutizim.app",
      "buildNumber": "1"
    }
  }
}
```

---

## 🏪 PLAY MARKET (Google Play Store)

### Kerakli narsalar:
1. **Google Play Console Account** ($25, bir martalik)
2. **APK/AAB file** (EAS yoki Emergent build dan)
3. **Screenshots** (kamida 2 ta, 1080x1920)
4. **App icon** (512x512)
5. **Feature graphic** (1024x500)
6. **Privacy Policy URL** (majburiy)
7. **Tavsif** (ingliz va o'zbek tilda)

### Qadamlar:

**1. Account yaratish:**
- https://play.google.com/console ga o'ting
- $25 to'lang
- Developer profile to'ldiring

**2. App yaratish:**
- "Create app" tugmasini bosing
- App name: `Edu Tizim`
- Default language: `Uzbek (uz-UZ)`
- App or game: `App`
- Free or paid: `Free`

**3. Store Listing to'ldirish:**

**Short description (80 char):**
```
O'quv markazlar uchun zamonaviy boshqaruv tizimi
```

**Full description:**
```
🎓 Edu Tizim - O'zbekistondagi o'quv markazlar uchun zamonaviy va to'liq boshqaruv tizimi.

✨ XUSUSIYATLARI:
• O'quv markaz to'liq boshqaruvi
• Guruhlar va o'quvchilar boshqaruvi
• Ustozlar va dars jadvali
• Avtomatik balans hisob-kitobi
• Coin tizimi va do'kon
• Reyting tizimi
• Davomat hisobi
• Telegram orqali xavfsiz login

🎯 4 TA ROLLAR:
• O'quv Markaz Admini (Boss)
• Ustozlar
• O'quvchilar
• Ota-onalar

📱 Ilova tezkor, ishonchli va foydalanish uchun qulay!
```

**4. Content Rating:**
- Questionnaire to'ldiring
- Target audience: 18+

**5. Privacy Policy:**

Privacy Policy yarating (https://www.privacypolicies.com/ orqali) va URL ni qo'shing.

**6. APK upload:**
- Production > Create new release
- APK upload qiling
- Release notes yozing
- "Start rollout to Production"

**7. Review:**
- 1-7 kun ichida Google ko'rib chiqadi
- Tasdiqlangach Play Store'da paydo bo'ladi

---

## 📦 ZIP FAYL YARATISH

Loyihani ZIP qilish:

```bash
cd /app
zip -r edu-tizim-full.zip . \
  -x "*/node_modules/*" \
  -x "*/\.git/*" \
  -x "*/__pycache__/*" \
  -x "*.log"
```

Yoki faqat asosiy fayllar:

```bash
cd /app
zip -r edu-tizim-source.zip \
  backend/ \
  frontend/app/ \
  frontend/assets/ \
  frontend/src/ \
  frontend/scripts/ \
  frontend/package.json \
  frontend/app.json \
  frontend/tsconfig.json \
  frontend/eslint.config.js \
  frontend/metro.config.js \
  README_FINAL.md \
  -x "*/node_modules/*"
```

---

## 📊 LOYIHANING ARXITEKTURASI

```
EDU TIZIM/
├── 🌐 backend/                  # FastAPI Backend
│   ├── server.py                # Asosiy API (admin, boss, teacher, student)
│   ├── seed_data.py             # Test data yaratish
│   ├── requirements.txt         # Python kutubxonalar
│   └── .env                     # MongoDB URL
│
├── 📱 frontend/                 # Expo Mobile App
│   ├── app/                     # Sahifalar (Expo Router)
│   │   ├── index.tsx                  # Role tanlash + Login
│   │   ├── _layout.tsx                # Stack navigation
│   │   ├── dashboard.tsx              # Boss dashboard
│   │   ├── rooms.tsx                  # Xonalar
│   │   ├── groups.tsx                 # Guruhlar
│   │   ├── teachers.tsx               # Ustozlar
│   │   ├── courses.tsx                # Kurslar
│   │   ├── students.tsx               # O'quvchilar
│   │   ├── store.tsx                  # Do'kon (Boss)
│   │   ├── teacher-dashboard.tsx      # Ustoz dashboard
│   │   ├── teacher-group.tsx          # Ustoz guruh + davomat
│   │   ├── student-dashboard.tsx      # O'quvchi dashboard
│   │   ├── student-calendar.tsx       # Kalendar
│   │   ├── student-ranking.tsx        # Reyting
│   │   ├── student-store.tsx          # O'quvchi do'kon
│   │   └── student-profile.tsx        # Profil
│   ├── package.json
│   ├── app.json                 # Expo config
│   └── .env                     # API URL
│
└── README_FINAL.md              # Bu fayl
```

---

## 🔑 TELEGRAM BOT SETUP

1. **Bot link:** https://t.me/EduTizimBot (yoki sizning bot username)

2. **Setup commands** (BotFather'da):
```
/setcommands
start - Botni ishga tushirish
help - Yordam
```

3. **Webhook setup:**
```bash
curl "https://api.telegram.org/bot8922878571:AAHMRa1Atm4cawMYaJG73joIkdO_QoWDXyo/setWebhook?url=https://YOUR_BACKEND_URL/api/telegram/webhook"
```

---

## 🐛 DEBUGGING

### Backend logs:
```bash
sudo supervisorctl tail -f backend
```

### Frontend logs:
```bash
sudo supervisorctl tail -f expo
```

### MongoDB:
```bash
mongosh
use test_database
db.education_centers.find()
db.students.find()
```

### Restart:
```bash
sudo supervisorctl restart all
```

---

## 📞 SUPPORT VA QO'SHIMCHA

### Tariff Limitlar:
- **Pro (200,000 so'm/oy):** 100 o'quvchi, 5 guruh, 5 ustoz
- **Pro+ (500,000 so'm/oy):** 300 o'quvchi, 50 guruh, 50 ustoz
- **VIP:** Cheksiz

### Avtomatik Balans Yechish:
- Har bir o'quvchi dars kuni keladi → balansdan kurs narxining (1/dars_soni) qismi yechiladi
- Misol: Kurs 300,000 so'm, oyiga 30 dars = 10,000 so'm/dars
- Faqat dars kunlarida pul yechiladi
- Muzlatilgan o'quvchidan pul yechilmaydi

### Coin Tizimi:
- Ustoz darsda qatnashgan o'quvchiga coin beradi (5-10 coin)
- O'quvchi coinlarni yig'ib do'kondan narsa sotib oladi
- Buyurtma berilgach, Boss panelda ko'rinadi va beriladi

---

## 🎯 KEYINGI QADAMLAR

1. ✅ **Test qilish** - Barcha funksiyalarni sinab ko'ring
2. ⏳ **Railway'ga deploy** - Yuqoridagi yo'riqnomaga amal qiling
3. ⏳ **APK build** - Emergent Publish yoki EAS orqali
4. ⏳ **Play Store'ga qo'yish** - Google Play Console orqali
5. ⏳ **Telegram bot real ulanish** - Webhook setup

---

## ✨ MUHIM ESLATMALAR

1. **Telegram Bot:** Bot token allaqachon backend'da. Webhook'ni Railway URL bilan sozlash kerak.

2. **Image Upload:** Hozir base64 formatda. Production uchun Cloudinary tavsiya qilinadi.

3. **Password Security:** Barcha parollar bcrypt bilan hash qilingan.

4. **MongoDB:** Production uchun MongoDB Atlas yoki Railway MongoDB tavsiya qilinadi.

5. **Bog'liqliklar:**
   - Backend: FastAPI, Motor (MongoDB), python-telegram-bot, bcrypt
   - Frontend: Expo 54, React Native, axios, expo-router

---

**Yaratilgan sanasi:** 2025  
**Versiya:** 1.0.0  
**Litsenziya:** Private

🎉 **Loyiha to'liq tayyor! Deploy qilishingiz va Play Store'ga joylashtirishingiz mumkin!**
