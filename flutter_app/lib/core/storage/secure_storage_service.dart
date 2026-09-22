import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../constants/app_constants.dart';

/// Secure enclave storage service for JWT tokens and sensitive user identifiers.
class SecureStorageService {
  final FlutterSecureStorage _storage;

  SecureStorageService({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(
                encryptedSharedPreferences: true,
              ),
              iOptions: IOSOptions(
                accessibility: KeychainAccessibility.first_unlock,
              ),
            );

  Future<void> saveTokens({
    required String accessToken,
    String? refreshToken,
  }) async {
    await _storage.write(key: AppConstants.keyAccessToken, value: accessToken);
    if (refreshToken != null) {
      await _storage.write(key: AppConstants.keyRefreshToken, value: refreshToken);
    }
  }

  Future<String?> getAccessToken() async {
    return await _storage.read(key: AppConstants.keyAccessToken);
  }

  Future<String?> getRefreshToken() async {
    return await _storage.read(key: AppConstants.keyRefreshToken);
  }

  Future<void> saveUserMetadata({
    required String userId,
    required String email,
  }) async {
    await _storage.write(key: AppConstants.keyUserId, value: userId);
    await _storage.write(key: AppConstants.keyUserEmail, value: email);
  }

  Future<String?> getUserId() async {
    return await _storage.read(key: AppConstants.keyUserId);
  }

  Future<String?> getUserEmail() async {
    return await _storage.read(key: AppConstants.keyUserEmail);
  }

  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}
