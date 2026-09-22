import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/secure_storage_service.dart';
import '../domain/auth_repository.dart';
import '../data/auth_repository_impl.dart';

// Core Service Providers
final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(secureStorage: storage);
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  final storage = ref.watch(secureStorageProvider);
  return AuthRepositoryImpl(apiClient: client, secureStorage: storage);
});

// Authentication State Notifier
class AuthStateNotifier extends AsyncNotifier<UserSession?> {
  @override
  Future<UserSession?> build() async {
    final repo = ref.watch(authRepositoryProvider);
    return await repo.restoreSession();
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(authRepositoryProvider);
      return await repo.login(email: email, password: password);
    });
  }

  Future<void> signup(String email, String password, {String? fullName}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(authRepositoryProvider);
      return await repo.signup(email: email, password: password, fullName: fullName);
    });
  }

  Future<void> logout() async {
    state = const AsyncValue.loading();
    final repo = ref.read(authRepositoryProvider);
    await repo.logout();
    state = const AsyncValue.data(null);
  }
}

final authStateProvider = AsyncNotifierProvider<AuthStateNotifier, UserSession?>(() {
  return AuthStateNotifier();
});
