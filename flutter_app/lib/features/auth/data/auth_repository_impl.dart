import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../../../core/errors/exceptions.dart';
import '../domain/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _apiClient;
  final SecureStorageService _secureStorage;

  AuthRepositoryImpl({
    required ApiClient apiClient,
    required SecureStorageService secureStorage,
  })  : _apiClient = apiClient,
        _secureStorage = secureStorage;

  @override
  Future<UserSession> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.login,
        data: {'email': email, 'password': password},
      );

      final token = response['access_token'] as String;
      final user = response['user'] as Map<String, dynamic>? ?? {};
      final userId = user['id']?.toString() ?? email;
      final fullName = user['full_name'] as String?;

      await _secureStorage.saveTokens(accessToken: token);
      await _secureStorage.saveUserMetadata(userId: userId, email: email);

      return UserSession(
        userId: userId,
        email: email,
        fullName: fullName,
        token: token,
      );
    } catch (e) {
      if (e is AppException) rethrow;
      throw AppException('Login failed: $e');
    }
  }

  @override
  Future<UserSession> signup({
    required String email,
    required String password,
    String? fullName,
  }) async {
    try {
      final response = await _apiClient.post(
        ApiConstants.signup,
        data: {
          'email': email,
          'password': password,
          if (fullName != null) 'full_name': fullName,
        },
      );

      final token = response['access_token'] as String;
      final user = response['user'] as Map<String, dynamic>? ?? {};
      final userId = user['id']?.toString() ?? email;

      await _secureStorage.saveTokens(accessToken: token);
      await _secureStorage.saveUserMetadata(userId: userId, email: email);

      return UserSession(
        userId: userId,
        email: email,
        fullName: fullName,
        token: token,
      );
    } catch (e) {
      if (e is AppException) rethrow;
      throw AppException('Signup failed: $e');
    }
  }

  @override
  Future<UserSession?> restoreSession() async {
    final token = await _secureStorage.getAccessToken();
    final userId = await _secureStorage.getUserId();
    final email = await _secureStorage.getUserEmail();

    if (token == null || token.isEmpty || userId == null || email == null) {
      return null;
    }

    try {
      // Validate session with backend /me endpoint
      await _apiClient.get(ApiConstants.me);
      return UserSession(
        userId: userId,
        email: email,
        token: token,
      );
    } catch (_) {
      // Session is invalid or expired
      await _secureStorage.clearAll();
      return null;
    }
  }

  @override
  Future<void> logout() async {
    try {
      await _apiClient.post(ApiConstants.logout);
    } catch (_) {
      // Best-effort remote logout
    } finally {
      await _secureStorage.clearAll();
    }
  }
}
