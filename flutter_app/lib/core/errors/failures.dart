import 'exceptions.dart';

/// Sealed hierarchy of typed business failures presented to the presentation layer.
sealed class Failure {
  final String message;
  final String? code;

  const Failure(this.message, {this.code});

  @override
  String toString() => '$runtimeType: $message';
}

class NetworkFailure extends Failure {
  const NetworkFailure([String message = 'No internet connection detected. Offline cache active.'])
      : super(message, code: 'NETWORK_ERROR');
}

class AuthenticationFailure extends Failure {
  const AuthenticationFailure([String message = 'Your session has expired. Please sign in again.'])
      : super(message, code: 'AUTH_ERROR');
}

class ValidationFailure extends Failure {
  const ValidationFailure(String message)
      : super(message, code: 'VALIDATION_ERROR');
}

class ServerFailure extends Failure {
  const ServerFailure([String message = 'The financial server is experiencing technical difficulties.'])
      : super(message, code: 'SERVER_ERROR');
}

class TimeoutFailure extends Failure {
  const TimeoutFailure([String message = 'The network request timed out. Please retry.'])
      : super(message, code: 'TIMEOUT_ERROR');
}

class ParsingFailure extends Failure {
  const ParsingFailure([String message = 'Received unrecognized data format from backend.'])
      : super(message, code: 'PARSING_ERROR');
}

class CacheFailure extends Failure {
  const CacheFailure([String message = 'Local database access failure.'])
      : super(message, code: 'CACHE_ERROR');
}

class UnknownFailure extends Failure {
  const UnknownFailure([String message = 'An unexpected error occurred. Please try again.'])
      : super(message, code: 'UNKNOWN_ERROR');
}

/// Mapper from low-level exceptions into strongly-typed domain failures.
Failure mapExceptionToFailure(Object error) {
  if (error is AuthException) {
    return AuthenticationFailure(error.message);
  } else if (error is NetworkException) {
    return NetworkFailure(error.message);
  } else if (error is TimeoutException) {
    return TimeoutFailure(error.message);
  } else if (error is ValidationException) {
    return ValidationFailure(error.message);
  } else if (error is ServerException) {
    return ServerFailure(error.message);
  } else if (error is ParsingException) {
    return ParsingFailure(error.message);
  } else if (error is CacheException) {
    return CacheFailure(error.message);
  } else {
    return UnknownFailure(error.toString());
  }
}
