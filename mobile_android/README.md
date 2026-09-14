# JARVIS Android Companion App Wrapper

This directory contains the native Android wrapper project for the **JARVIS Mobile Companion**.

### Two Ways to Use on Your Phone:

#### Option 1: Instant PWA (Recommended - No Compilation Needed)
1. Ensure your phone and PC are connected to the same Wi-Fi network (or Tailscale VPN).
2. Start the JARVIS server on your PC (or double-click `Pair_Mobile.bat` on your Desktop).
3. Point your phone's camera at the displayed QR code (or open `http://192.168.1.4:8000/app`).
4. When prompted by Chrome or Safari, tap **"Add to Home Screen"** or **"Install App"**.
5. JARVIS will install as a native, fullscreen app with Arc Reactor icon on your phone!

#### Option 2: Native Android APK (Using Android Studio)
1. Open this folder (`mobile_android`) in Android Studio.
2. Update the host IP in `MainActivity.java` if needed.
3. Click **Build > Build Bundle(s) / APK(s) > Build APK(s)**.
4. Install the generated `app-debug.apk` onto your Android phone.
