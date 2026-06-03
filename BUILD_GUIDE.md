# SmartEdu Apps - APK Qilish Yo'riqnomasi

## 4 ta ilova mavjud:

| Ilova | Papka | Rol | Rang |
|-------|-------|-----|------|
| SmartEdu Moderator | `smartedu-moderator/` | Boss/Admin | Ko'k |
| SmartEdu Teachers | `smartedu-teachers/` | Ustoz | Yashil |
| SmartEdu Parents | `smartedu-parents/` | Ota-ona | Qizil |
| SmartEdu Students | `smartedu-students/` | O'quvchi | Ko'k-havorang |

---

## APK Qilish Usullari

### 1-usul: EAS Build (Tavsiya etiladi - Eng oson)

**Bir marta sozlash:**
```bash
npm install -g @expo/eas-cli
eas login   # expo.dev da hisob kerak
```

**Har bir ilova uchun:**
```bash
cd smartedu-moderator
npm install
eas build --platform android --profile preview
```

`preview` profili APK beradi (Play Store uchun emas).

**eas.json yarating:**
```json
{
  "build": {
    "preview": {
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      }
    }
  }
}
```

---

### 2-usul: Local Build (Android Studio kerak)

**Talab:**
- Android Studio
- Java 17
- Node.js 18+

**Qadamlar:**
```bash
cd smartedu-moderator
npm install
npx expo prebuild --platform android
cd android
./gradlew assembleDebug    # Debug APK
# yoki
./gradlew assembleRelease  # Release APK (sign kerak)
```

**APK manzili:** `android/app/build/outputs/apk/debug/app-debug.apk`

---

### 3-usul: Expo Go (Test uchun, APK emas)
```bash
cd smartedu-moderator
npm install
npx expo start
```
QR kodni Expo Go ilovasida scan qiling.

---

## Muhim Fayllar

Har bir ilovada:
- `app.json` - Ilova nomi, package name, icon
- `.env` - Backend URL: `https://smart-edu.up.railway.app`
- `assets/images/icon.png` - Ilova belgisi

---

## Backend & Bot

- **Backend URL:** https://smart-edu.up.railway.app
- **Telegram Bot:** @SmartEduVerificationBot (kod yuboradi)

---

## Katta Admin Panel (Sayt)

Oquv markazlar yaratish uchun sayt - bu alohida.
Sayt orqali oquv markazlar qo'shiladi, keyin:
- Boss o'z markazi uchun **SmartEdu Moderator** APK dan foydalanadi
- Ustozlar **SmartEdu Teachers** APK dan
- Ota-onalar **SmartEdu Parents** APK dan
- O'quvchilar **SmartEdu Students** APK dan
