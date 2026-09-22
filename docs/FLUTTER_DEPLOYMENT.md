# FinMate 2.0 Mobile: Deployment & Release Guide

## 1. Environment Configurations

FinMate 2.0 supports three operational environments configured via compile-time `--dart-define` flags:

* **Development**:
  ```bash
  flutter run --dart-define=APP_ENV=dev --dart-define=API_BASE_URL=http://10.0.2.2:8000
  ```
* **Staging**:
  ```bash
  flutter run --dart-define=APP_ENV=staging --dart-define=API_BASE_URL=https://staging-api.finmate.internal
  ```
* **Production**:
  ```bash
  flutter run --dart-define=APP_ENV=prod --dart-define=API_BASE_URL=https://api.finmate.internal
  ```

---

## 2. Release Builds

### Android Release APK
```bash
flutter build apk --release --obfuscate --split-debug-info=./build/symbols
```

### Android App Bundle (AAB for Google Play)
```bash
flutter build appbundle --release --obfuscate --split-debug-info=./build/symbols
```

### iOS Release IPA
```bash
flutter build ipa --release
```

---

## 3. Security Hardening Checklist

- [x] JWT tokens stored strictly in hardware-backed `FlutterSecureStorage` (Keychain / Android Keystore).
- [x] Zero hardcoded secrets, database credentials, or Gemini API keys in mobile code.
- [x] TLS 1.3 enforced for all network communication with certificate validation enabled.
- [x] Code obfuscation enabled for release builds.
