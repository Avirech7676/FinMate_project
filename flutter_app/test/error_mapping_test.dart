import 'package:test/test.dart';
import '../lib/core/errors/exceptions.dart';
import '../lib/core/errors/failures.dart';

void main() {
  group('FinMate 2.0 Error & Failure Mapping Tests', () {
    test('mapExceptionToFailure maps AuthException to AuthenticationFailure', () {
      const ex = AuthException('Invalid email or password', 401);
      final failure = mapExceptionToFailure(ex);
      expect(failure, isA<AuthenticationFailure>());
      expect(failure.message, contains('Invalid email or password'));
      expect(failure.code, equals('AUTH_ERROR'));
    });

    test('mapExceptionToFailure maps NetworkException to NetworkFailure', () {
      const ex = NetworkException('No route to host');
      final failure = mapExceptionToFailure(ex);
      expect(failure, isA<NetworkFailure>());
      expect(failure.code, equals('NETWORK_ERROR'));
    });

    test('mapExceptionToFailure maps ServerException to ServerFailure', () {
      const ex = ServerException('Internal database deadlock', 500);
      final failure = mapExceptionToFailure(ex);
      expect(failure, isA<ServerFailure>());
      expect(failure.code, equals('SERVER_ERROR'));
    });

    test('mapExceptionToFailure maps unknown exceptions to UnknownFailure', () {
      final failure = mapExceptionToFailure(Exception('Random glitch'));
      expect(failure, isA<UnknownFailure>());
      expect(failure.code, equals('UNKNOWN_ERROR'));
    });
  });
}
