import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/errors/failures.dart';

class UserSession {
  final String userId;
  final String email;
  final String? fullName;
  final String token;

  const UserSession({
    required this.userId,
    required this.email,
    this.fullName,
    required this.token,
  });
}

abstract class AuthRepository {
  Future<UserSession> login({required String email, required String password});
  Future<UserSession> signup({required String email, required String password, String? fullName});
  Future<UserSession?> restoreSession();
  Future<void> logout();
}
