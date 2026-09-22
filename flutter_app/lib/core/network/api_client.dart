import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../storage/secure_storage_service.dart';
import '../errors/exceptions.dart';
import 'interceptors.dart';

/// Centralized HTTP API client wrapping Dio with authentication, timeout handling,
/// cancellation tokens, and structured exception conversion.
class ApiClient {
  late final Dio _dio;
  final SecureStorageService _secureStorage;

  ApiClient({
    required SecureStorageService secureStorage,
    Dio? customDio,
    String? baseUrl,
  }) : _secureStorage = secureStorage {
    _dio = customDio ??
        Dio(
          BaseOptions(
            baseUrl: baseUrl ?? EnvironmentConfig.baseUrl,
            connectTimeout: ApiConstants.connectTimeout,
            receiveTimeout: ApiConstants.receiveTimeout,
            sendTimeout: ApiConstants.sendTimeout,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
          ),
        );

    _dio.interceptors.addAll([
      AuthInterceptor(_secureStorage),
      ErrorInterceptor(),
    ]);
  }

  void updateBaseUrl(String url) {
    _dio.options.baseUrl = url;
  }

  Future<dynamic> get(
    String path, {
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
        cancelToken: cancelToken,
      );
      return response.data;
    } on DioException catch (e) {
      if (e.error is AppException) throw e.error!;
      throw AppException(e.message ?? 'HTTP GET failed');
    }
  }

  Future<dynamic> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
        cancelToken: cancelToken,
      );
      return response.data;
    } on DioException catch (e) {
      if (e.error is AppException) throw e.error!;
      throw AppException(e.message ?? 'HTTP POST failed');
    }
  }

  Future<dynamic> put(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.put(
        path,
        data: data,
        queryParameters: queryParameters,
        cancelToken: cancelToken,
      );
      return response.data;
    } on DioException catch (e) {
      if (e.error is AppException) throw e.error!;
      throw AppException(e.message ?? 'HTTP PUT failed');
    }
  }

  Future<dynamic> delete(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.delete(
        path,
        data: data,
        queryParameters: queryParameters,
        cancelToken: cancelToken,
      );
      return response.data;
    } on DioException catch (e) {
      if (e.error is AppException) throw e.error!;
      throw AppException(e.message ?? 'HTTP DELETE failed');
    }
  }

  Future<dynamic> uploadMultipart(
    String path, {
    required FormData formData,
    ProgressCallback? onSendProgress,
    CancelToken? cancelToken,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: formData,
        onSendProgress: onSendProgress,
        cancelToken: cancelToken,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
        ),
      );
      return response.data;
    } on DioException catch (e) {
      if (e.error is AppException) throw e.error!;
      throw AppException(e.message ?? 'Multipart upload failed');
    }
  }
}
