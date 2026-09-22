import 'package:dio/dio.dart';
import '../storage/secure_storage_service.dart';
import '../errors/exceptions.dart';

/// Interceptor that attaches the JWT Bearer token to all outbound API requests.
class AuthInterceptor extends QueuedInterceptor {
  final SecureStorageService _secureStorage;

  AuthInterceptor(this._secureStorage);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip token injection for public authentication endpoints
    final path = options.path;
    if (path.contains('/auth/login') || path.contains('/auth/signup')) {
      return handler.next(options);
    }

    try {
      final token = await _secureStorage.getAccessToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    } catch (_) {
      // Proceed without token if secure storage fails
    }

    return handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Clear expired credentials
      await _secureStorage.clearAll();
      return handler.reject(
        DioException(
          requestOptions: err.requestOptions,
          response: err.response,
          type: DioExceptionType.badResponse,
          error: const AuthException('Session expired or unauthorized. Please log in again.'),
        ),
      );
    }
    return handler.next(err);
  }
}

/// Centralized error translation interceptor mapping Dio exceptions to domain [AppException]s.
class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    AppException exception;

    switch (err.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        exception = const TimeoutException();
        break;

      case DioExceptionType.connectionError:
        exception = const NetworkException();
        break;

      case DioExceptionType.badResponse:
        final statusCode = err.response?.statusCode;
        final data = err.response?.data;
        String message = 'Server returned error status $statusCode';

        if (data is Map<String, dynamic>) {
          if (data.containsKey('detail')) {
            final detail = data['detail'];
            message = detail is String ? detail : detail.toString();
          } else if (data.containsKey('message')) {
            message = data['message'].toString();
          }
        }

        if (statusCode == 401 || statusCode == 403) {
          exception = AuthException(message, statusCode);
        } else if (statusCode == 422) {
          exception = ValidationException(message, statusCode, data);
        } else if (statusCode != null && statusCode >= 500) {
          exception = ServerException(message, statusCode, data);
        } else {
          exception = AppException(message, statusCode: statusCode, details: data);
        }
        break;

      case DioExceptionType.cancel:
        exception = const AppException('Request was cancelled.');
        break;

      default:
        exception = AppException(err.message ?? 'Unknown network failure');
    }

    return handler.reject(
      DioException(
        requestOptions: err.requestOptions,
        response: err.response,
        type: err.type,
        error: exception,
      ),
    );
  }
}
