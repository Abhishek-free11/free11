# FREE11 — Google Play Store Submission Guide
## Complete Step-by-Step Guide (Feb 2026)

---

## WHAT'S ALREADY DONE FOR YOU

| Item | Status |
|------|--------|
| Android TWA project code | READY |
| App icons (all 5 mipmap sizes) | READY |
| Splash screen logo | READY |
| Play Store icon (512x512) | READY in `play_store_assets/` |
| Feature graphic (1024x500) | READY in `play_store_assets/` |
| App screenshots (2) | READY in `play_store_assets/` |
| Store listing text | READY in `play_store_listing.txt` |
| AndroidManifest.xml | READY |
| Firebase / AdMob wired in | READY |

---

## WHAT YOU NEED TO DO (In Order)

---

## STEP 1 — Prerequisites (5 mins)

Install on your local machine:
- **Android Studio Hedgehog** (2023.1.1) or newer: https://developer.android.com/studio
- **Java 17 JDK**: https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html
- **Git** (to clone/download the project)

---

## STEP 2 — Download the Project

Copy the entire `/app/android-twa/` folder to your local machine.

---

## STEP 3 — Generate Your Signing Keystore (ONE TIME — Keep it safe forever!)

Open your terminal and run:

```bash
keytool -genkey -v \
  -keystore free11.keystore \
  -alias free11key \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -dname "CN=FREE11, OU=Mobile, O=FREE11 Inc, L=Mumbai, S=Maharashtra, C=IN"
```

It will ask you to create a **keystore password** and a **key password**. Save both passwords somewhere safe (a password manager). You can NEVER recover them.

Then move the keystore file into the project:
```bash
cp free11.keystore android-twa/app/free11.keystore
```

**Get the SHA-256 fingerprint** (you need this for Step 4):
```bash
keytool -list -v -keystore free11.keystore -alias free11key
```
Look for the line: `SHA256: AA:BB:CC:...`  Copy the full value.

---

## STEP 4 — Update assetlinks.json

Open: `/app/frontend/public/.well-known/assetlinks.json`

Replace `REPLACE_WITH_YOUR_APK_RELEASE_SHA256_FINGERPRINT` with your real SHA-256 from Step 3:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.free11.app",
    "sha256_cert_fingerprints": [
      "AA:BB:CC:DD:EE:FF:..."
    ]
  }
}]
```

**Deploy your frontend** after this change so the file is live at:
`https://free11.com/.well-known/assetlinks.json`

You can verify it after deployment with:
```
https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://free11.com&relation=delegate_permission/common.handle_all_urls
```

---

## STEP 5 — Configure Signing in build.gradle

Open `android-twa/app/build.gradle` and uncomment + fill in the signing config:

```gradle
signingConfig signingConfigs.create("release") {
    storeFile file("free11.keystore")
    storePassword "YOUR_KEYSTORE_PASSWORD"
    keyAlias "free11key"
    keyPassword "YOUR_KEY_PASSWORD"
}
```

---

## STEP 6 — Open in Android Studio & Sync

1. Open Android Studio
2. File → Open → select the `android-twa/` folder
3. Wait for Gradle sync (downloads ~500MB of dependencies first time)
4. If any errors appear, click "Try Again" or "Sync Now"

---

## STEP 7 — Build the Release AAB

In Android Studio terminal (or your system terminal inside the android-twa folder):

```bash
./gradlew bundleRelease
```

On Windows:
```
gradlew.bat bundleRelease
```

Output file: `android-twa/app/build/outputs/bundle/release/app-release.aab`

This is the file you upload to Play Console.

---

## STEP 8 — Test Before Submitting (Recommended)

Build a debug APK first to test on your device:
```bash
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Check:
- App opens in full-screen (no browser URL bar visible)
- Homepage loads correctly
- Navigation works
- AdMob ads appear (test ads in debug mode)

---

## STEP 9 — Create Google Play Console Account

1. Go to: https://play.google.com/console/signup
2. Pay the $25 one-time registration fee
3. Complete identity verification

---

## STEP 10 — Create Your App in Play Console

1. Click **"Create app"**
2. App name: `FREE11`
3. Default language: `English (India)` or `Hindi`
4. App or Game: **App**
5. Free or Paid: **Free**
6. Accept declarations → Create app

---

## STEP 11 — Fill Store Listing

Go to **Store Presence → Main store listing**

Use the content from `play_store_assets/play_store_listing.txt`

Upload these files from `play_store_assets/`:
- **App icon**: `icon_512x512.png` (512×512)
- **Feature graphic**: `feature_graphic_1024x500.png` (1024×500)
- **Phone screenshots**: `screenshot_01_predict.png`, `screenshot_02_shop.png`

---

## STEP 12 — Set Up App Content

Go to **Policy → App content**. Complete all sections:

### Privacy Policy
- URL: `https://free11.com/privacy` (create this page if not done)

### App Access
- Select: **"All or most functionality is accessible without special access"**

### Ads
- Does your app contain ads? **YES** (AdMob)

### Content Rating
Fill the questionnaire:
- No violence
- No sexual content
- No user-generated content
- No location sharing
- No personal/sensitive data (apart from account creation)
- Final rating: **Everyone** (ESRB: E)

### Target Audience
- Age group: **18 and over**
- No ads targeting children

### News App
- Not a news app: **No**

### COVID-19 Contact Tracing
- **No**

---

## STEP 13 — Upload Your AAB

Go to **Release → Production → Create new release**

1. Upload `app-release.aab`
2. Release name: `1.0.0`
3. Release notes:
```
Initial launch of FREE11 — India's skill-based cricket prediction app.
• Predict ball-by-ball cricket outcomes
• Earn free coins for correct predictions
• Redeem coins for real rewards
• Play card games: Rummy, Teen Patti, Poker, Solitaire
• Daily quests and challenges
```

---

## STEP 14 — Review & Submit

1. Complete all remaining green ticks in the **Dashboard**
2. Click **"Send for review"**
3. Google review typically takes **3–7 days** for new apps
4. You'll get an email when approved or if there are issues

---

## IMPORTANT NOTES

### On Content Policy
- Your app description clearly states: "No deposits, no cash wagering, rewards are promotional"
- The disclaimer in the app UI is compliant
- Do NOT use words like "bet", "wager", or "gambling" in store listing
- Category: **Sports** (not Games/Gambling)

### On Digital Asset Links (TWA requirement)
- If `assetlinks.json` is not correct, the app opens with a browser URL bar (not full-screen)
- This is the most common TWA submission issue — double-check Step 4

### On App Review
- First submission for new accounts often gets extra scrutiny
- Have your website live at `free11.com` before submitting
- Privacy Policy page must be live

---

## FILES READY FOR UPLOAD

```
play_store_assets/
├── icon_512x512.png           ← App icon (512×512)
├── feature_graphic_1024x500.png ← Feature graphic (1024×500)
├── screenshot_01_predict.png  ← Screenshot 1: Prediction screen
├── screenshot_02_shop.png     ← Screenshot 2: Shop/Rewards screen
└── play_store_listing.txt     ← All text content for store listing
```

```
app/src/main/res/
├── mipmap-mdpi/ic_launcher.png       (48×48)
├── mipmap-hdpi/ic_launcher.png       (72×72)
├── mipmap-xhdpi/ic_launcher.png      (96×96)
├── mipmap-xxhdpi/ic_launcher.png     (144×144)
├── mipmap-xxxhdpi/ic_launcher.png    (192×192)
├── mipmap-xxxhdpi/ic_launcher_round.png
└── drawable/ic_splash_logo.png       (512×512)
```

---

## TIMELINE ESTIMATE

| Task | Time |
|------|------|
| Install Android Studio + sync Gradle | 30-60 min |
| Generate keystore | 5 min |
| Update assetlinks.json + deploy | 10 min |
| Build AAB | 10 min |
| Fill Play Console listing | 30-45 min |
| Google review | 3-7 days |
| **Total to go live** | **~1 week** |
