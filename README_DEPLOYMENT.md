# EDU TIZIM - DEPLOYMENT VA APK GUIDE

## 🎯 LOYIHA HOLATI

### ✅ TO'LIQ TAYYOR:
1. **Backend API** (FastAPI + MongoDB) - 100%
2. **Admin Panel** (Web) - 100%  
3. **EDU BOSS Mobile App** - 100%

### ⏳ BOSHLANGAN:
4. **EDU TEACHER Mobile App** - 40%
5. **EDU STUDENT Mobile App** - 40%

---

## 📱 APK YARATISH

### Usul 1: Emergent Publish (TAVSIYA QILINADI)

1. Emergent Dashboard'da yuqori o'ng burchakdagi **"Publish"** tugmasini bosing
2. App type: **Android APK**
3. App name: **EDU Boss** (yoki boshqa nom)
4. Build boshlana di
5. Tayyor bo'lgach APK yuklab oling

### Usul 2: EAS Build (Qo'lda)

```bash
# EAS CLI o'rnatish
npm install -g eas-cli

# Expo account yaratish
eas login

# Loyihani configure qilish
cd /app/frontend
eas build:configure

# Android APK build
eas build --platform android --profile preview

# iOS IPA build (Mac kerak)
eas build --platform ios --profile preview
```

---

## 🚀 RAILWAY GA DEPLOY QILISH

### 1. Railway Account Yaratish
- https://railway.app ga o'ting
- GitHub bilan login qiling

### 2. Yangi Project Yaratish

```bash
# Railway CLI o'rnatish
npm install -g @railway/cli

# Login
railway login

# Yangi project
railway init

# MongoDB qo'shish
railway add

# Backend deploy
cd /app/backend
railway up

# Environment variables sozlash
railway variables set MONGO_URL="mongodb://..."
railway variables set DB_NAME="edu_tizim"
```

### 3. Domain Sozlash
- Railway dashboard'da Project Settings > Domains
- Custom domain qo'shish yoki railway.app subdomain ishlatish

---

## 🏪 PLAY STORE GA JOYLASHTIRISH

### Talab qilinadigan narsalar:
1. **Google Play Console Account** ($25 bir martalik to'lov)
2. **APK yoki AAB file** (EAS build dan)
3. **App ikona, screenshot'lar**
4. **Privacy Policy URL**
5. **App tavsifi (ingliz va o'zbek tilda)**

### Qadamlar:

#### 1. Google Play Console'da App Yaratish
- https://play.google.com/console ga o'ting
- "Create app" tugmasini bosing
- App nomi, kategoriya, til tanlang

#### 2. App Content To'ldirish
- **App content**: Privacy policy, target audience
- **Store listing**: Screenshots (min 2 ta), description, icon
- **Content rating**: Questionnaire to'ldirish

#### 3. Release Tayyorlash

**app.json ni to'ldirish:**
```json
{
  "expo": {
    "name": "EDU Boss",
    "slug": "edu-boss",
    "version": "1.0.0",
    "android": {
      "package": "com.yourcompany.eduboss",
      "versionCode": 1,
      "permissions": [
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ]
    }
  }
}
```

#### 4. APK Upload Qilish
- Play Console > Release > Production
- "Create new release"
- APK/AAB file yuklash
- Release notes yozish (o'zbek/ingliz)
- "Review release" > "Start rollout to Production"

#### 5. Review Jarayoni
- Google 1-7 kun ichida ko'rib chiqadi
- Muammolar bo'lsa email keladi
- Tasdiqlangach Play Store'da paydo bo'ladi

---

## 🔐 ADMIN PANEL KIRISH

**URL:** `http://your-backend-url/api/admin-panel`

**Test credentials:**
- Phone: 998901234567
- Password 1: admin123
- Password 2: admin456

---

## 📦 ZIP FAYL YARATISH

Butun loyihani ZIP qilish:

```bash
cd /app
zip -r edu-tizim-full.zip . -x "*/node_modules/*" "*/\.git/*" "*/__pycache__/*"
```

Faqat kerakli fayllar:

```bash
cd /app
zip -r edu-tizim.zip \
  backend/ \
  frontend/app/ \
  frontend/assets/ \
  frontend/package.json \
  frontend/app.json \
  frontend/tsconfig.json \
  README_DEPLOYMENT.md
```

---

## 🐛 DEBUGGING

### Backend Logs:
```bash
sudo supervisorctl tail -f backend
```

### Frontend Logs:
```bash
sudo supervisorctl tail -f expo
```

### MongoDB:
```bash
mongosh
use test_database
db.education_centers.find()
```

---

## 📞 SUPPORT

**Test Credentials:**
- Admin: 998901234567 / admin123 / admin456
- Boss: (Admin panelda yaratiladi)
- Teacher: (Boss tomonidan yaratiladi)
- Student: (Boss tomonidan yaratiladi)

**Telegram Bot Token:** 8922878571:AAHMRa1Atm4cawMYaJG73joIkdO_QoWDXyo

---

## ⚠️ ESLATMALAR

1. **Teacher va Student app'lari** hali to'liq tayyor emas. Ularni to'ldirish uchun qo'shimcha vaqt kerak.

2. **Telegram bot** hozirda faqat test code return qiladi. Real integration uchun bot yaratish va webhook sozlash kerak.

3. **Image uploads** base64 formatda saqlanadi. Production uchun S3/Cloudinary tavsiya qilinadi.

4. **Parollar** bcrypt bilan hash qilingan. Production uchun 2FA qo'shish tavsiya qilinadi.

5. **Tariff limits** backend'da tekshiriladi lekin enforce qilinmaydi. Bu funksiyani kengaytirish kerak.

---

## 🎉 KEYINGI QADAMLAR

1. ✅ Backend testing
2. ✅ Admin panel testing
3. ✅ Boss app testing
4. ⏳ Teacher app to'ldirish (3-4 soat)
5. ⏳ Student app to'ldirish (3-4 soat)
6. ⏳ Telegram bot real integration
7. ⏳ Full integration testing
8. ⏳ APK generation
9. ⏳ Railway deployment
10. ⏳ Play Store submission

---

**Yaratilgan sanasi:** 2025
**Backend:** FastAPI + MongoDB + Python Telegram Bot
**Frontend:** React Native + Expo Router
**Deployed on:** Railway (tavsiya qilinadi)
