/// API endpoints and configuration constants for FinMate 2.0 backend communication.
class ApiConstants {
  ApiConstants._();

  /// Default local development backend URL.
  /// For Android emulator, use 10.0.2.2.
  /// For physical device, replace with host LAN IP or configure via [EnvironmentConfig].
  static const String defaultBaseUrl = 'http://10.0.2.2:8000';
  static const String defaultLanUrl = 'http://localhost:8000';

  // Timeout thresholds
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 20);
  static const Duration sendTimeout = Duration(seconds: 15);

  // Authentication Endpoints
  static const String login = '/api/v1/auth/login';
  static const String signup = '/api/v1/auth/signup';
  static const String logout = '/api/v1/auth/logout';
  static const String me = '/api/v1/auth/me';

  // Transactions & Ingestion
  static const String transactions = '/api/v1/transactions';
  static const String uploadCsv = '/upload-csv';
  static const String scanReceipt = '/scan-receipt';

  // Analytics & Intelligence
  static const String analytics = '/api/v1/analytics';
  static const String overview = '/api/v1/analytics/overview';
  static const String anomalies = '/api/v1/intelligence/anomalies';
  static const String forecast = '/api/v1/intelligence/forecast';
  static const String healthScore = '/api/v1/intelligence/health-score';
  static const String cashFlow = '/api/v1/intelligence/cash-flow';
  static const String simulatePurchase = '/api/v1/intelligence/simulate-purchase';

  // Goals & Budget
  static const String goals = '/api/v1/goals';

  // AI Assistant & Reports
  static const String aiChat = '/api/v1/ai/chat';
  static const String weeklyBriefing = '/api/v1/reports/weekly-briefing';
  static const String exportData = '/api/v1/user/export-data';
  static const String deleteAccount = '/api/v1/user/account';
}

/// Environment configuration provider.
enum Environment { dev, staging, prod }

class EnvironmentConfig {
  static Environment current = Environment.dev;
  static String? _customBaseUrl;

  static void setCustomBaseUrl(String url) {
    _customBaseUrl = url;
  }

  static String get baseUrl {
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      return _customBaseUrl!;
    }
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl;

    switch (current) {
      case Environment.dev:
        return ApiConstants.defaultBaseUrl;
      case Environment.staging:
        return 'https://staging-api.finmate.internal';
      case Environment.prod:
        return 'https://api.finmate.internal';
    }
  }
}
