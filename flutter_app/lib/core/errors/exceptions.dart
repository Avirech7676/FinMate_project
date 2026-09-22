/// Typed low-level exceptions thrown within the data and network layers.
class AppException implements Exception {
  final String message;
  final int? statusCode;
  final dynamic details;

  const AppException(this.message, {this.statusCode, this.details});

  @override
  String toString() => 'AppException: $message (status: $statusCode)';
}

class NetworkException extends AppException {
  const NetworkException([String message = 'Unable to reach the server. Please check your connection.'])
      : super(message);
}

class TimeoutException extends AppException {
  const TimeoutException([String message = 'The request timed out. Please try again.'])
      : super(message);
}

class AuthException extends AppException {
  const AuthException([String message = 'Authentication failed. Please sign in again.', int? statusCode = 401])
      : super(message, statusCode: statusCode);
}

class ServerException extends AppException {
  const ServerException([String message = 'An unexpected server error occurred.', int? statusCode = 500, dynamic details])
      : super(message, statusCode: statusCode, details: details);
}

class ValidationException extends AppException {
  const ValidationException([String message = 'The submitted data was invalid.', int? statusCode = 422, dynamic details])
      : super(message, statusCode: statusCode, details: details);
}

class ParsingException extends AppException {
  const ParsingException([String message = 'Failed to parse response data.'])
      : super(message);
}

class CacheException extends AppException {
  const CacheException([String message = 'Failed to retrieve or store cached data.'])
      : super(message);
}
