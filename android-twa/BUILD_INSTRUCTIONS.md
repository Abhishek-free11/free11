# FREE11 Android TWA — Build Instructions

## Prerequisites
- Android Studio Hedgehog (2023.1.1) or newer
- Java 17 JDK
- Android SDK Build-Tools 34+

---

## Step 1: Open Project in Android Studio

1. Open Android Studio
2. Select **File → Open**
3. Navigate to this `android-twa/` folder and click **Open**
4. Wait for Gradle sync to complete (downloads dependencies automatically)

---

## Step 2: Set Up Signing Key

Generate a release keystore (do this once, keep it safe):
```bash
keytool -genkey -v -keystore free11.keystore \
  -alias free11key \
  -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -dname "CN=FREE11, OU=Mobile, O=FREE11 Inc, L=Mumbai, S=Maharashtra, C=IN"
```

Copy `free11.keystore` to `android-twa/app/` and uncomment the signing config in `app/build.gradle`.

Get the SHA-256 fingerprint:
```bash
keytool -list -v -keystore free11.keystore -alias free11key
# Copy the SHA256 fingerprint — you need it for assetlinks.json
```

---

## Step 3: Configure assetlinks.json

1. Copy the SHA-256 fingerprint from Step 2
2. Update `/frontend/public/.well-known/assetlinks.json`:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.free11.app",
    "sha256_cert_fingerprints": [
      "AA:BB:CC:DD:..." 
    ]
  }
}]
```
3. Deploy this file to your server so it's accessible at:
   `https://free11.com/.well-known/assetlinks.json`

---

## Step 4: Add App Icon

Place your icon files in the correct directories:
```
app/src/main/res/
├── mipmap-mdpi/ic_launcher.png         (48x48)
├── mipmap-hdpi/ic_launcher.png         (72x72)
├── mipmap-xhdpi/ic_launcher.png        (96x96)
├── mipmap-xxhdpi/ic_launcher.png       (144x144)
├── mipmap-xxxhdpi/ic_launcher.png      (192x192)
└── drawable/ic_splash_logo.png         (512x512, for splash screen)
```

Use Android Studio's **Asset Studio** (right-click res → New → Image Asset) to generate all sizes from your FREE11 icon.

---

## Step 5: Add Splash Screen Logo

Place `ic_splash_logo.png` (512x512, transparent background) in:
`app/src/main/res/drawable/ic_splash_logo.png`

---

## Step 6: Build Debug APK

In Android Studio:
- **Build → Build Bundle(s) / APK(s) → Build APK(s)**
- APK location: `app/build/outputs/apk/debug/app-debug.apk`

Or via terminal:
```bash
./gradlew assembleDebug
```

---

## Step 7: Build Release AAB (for Play Store)

```bash
./gradlew bundleRelease
```
Output: `app/build/outputs/bundle/release/app-release.aab`

---

## Step 8: Test on Device

```bash
# Install debug APK on connected device
adb install app/build/outputs/apk/debug/app-debug.apk

# Verify TWA is working (app should open in full-screen, no browser chrome)
# If browser chrome shows, assetlinks.json is not verified yet
```

---

## Step 9: Disable PWA Install Prompt

The TWA automatically detects it's running inside the Android app via the `display-mode: standalone` media query.

Add this to your React app to disable the PWA install prompt when inside TWA:
```javascript
// In your index.js or App.js
const isRunningInTWA = document.referrer.includes('android-app://com.free11.app');
if (isRunningInTWA) {
  window.addEventListener('beforeinstallprompt', (e) => e.preventDefault());
}
```

This is already handled in the app via the `navigator.standalone` check.

---

## Google Play Store Submission Checklist

### Required Assets
- [ ] App icon: 512x512 PNG (no alpha)
- [ ] Feature graphic: 1024x500 PNG
- [ ] Screenshots: min 2, recommended 8 (phone + tablet)
- [ ] Short description (80 chars): "Predict cricket. Earn coins. Get real products."
- [ ] Full description (4000 chars): [see play_store_description.txt]

### App Content Rating
- Rating: Everyone (no violence, no gambling, age 18+ enforced in-app)
- Content: Sports, Social

### Target Audience
- Primary: 18-35 years
- Geography: India

### Category
- Primary: Sports
- Secondary: Entertainment

---

## Play Store Description Template

**Short description:**
Predict cricket ball-by-ball. Earn Free Coins. Redeem for real vouchers.

**Full description:**
FREE11 is India's Social Entertainment Sports Platform where cricket knowledge = real rewards.

🏏 **How it works:**
• Predict ball-by-ball outcomes during live cricket matches
• Earn Free Coins for correct predictions
• Redeem coins for Swiggy, Amazon, Netflix vouchers and more

🎯 **100% Skill-Based:**
• Your accuracy determines your rank
• No real money required
• Free to play, forever

⚡ **What you get:**
• Live match predictions with instant coin rewards
• Daily check-in streak bonuses
• Spin wheel, scratch cards, cricket quiz
• Squad leagues with friends
• Real product voucher redemptions

📋 **Important:**
• FREE11 is NOT a gambling or betting platform
• Free Coins have no monetary value
• Available for 18+ users in eligible Indian states
• Skill-based entertainment platform

Join millions of cricket fans. Make the right calls. Get real products.
