/// Application-wide constants and storage keys.
class AppConstants {
  AppConstants._();

  static const String appName = 'FinMate 2.0';
  static const String appVersion = '2.0.0';

  // Secure Storage Keys
  static const String keyAccessToken = 'finmate_access_token';
  static const String keyRefreshToken = 'finmate_refresh_token';
  static const String keyUserId = 'finmate_user_id';
  static const String keyUserEmail = 'finmate_user_email';

  // Shared Cache Keys
  static const String keyOfflineSyncQueue = 'finmate_offline_sync_queue';
  static const String keyCachedTransactions = 'finmate_cached_transactions';
  static const String keyCachedOverview = 'finmate_cached_overview';
  static const String keyCachedHealthScore = 'finmate_cached_health_score';

  // Default limits
  static const int defaultPageSize = 25;
  static const int maxOfflineQueueSize = 500;
}
