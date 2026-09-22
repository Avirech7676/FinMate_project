import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/storage/local_cache_service.dart';
import '../../../core/network/connectivity_service.dart';
import '../../auth/presentation/auth_providers.dart';
import '../../../shared/models/financial_overview.dart';
import '../../../shared/models/anomaly.dart';
import '../../../shared/models/forecast.dart';
import '../../../shared/models/health_score.dart';
import '../../../shared/models/cash_flow_projection.dart';
import '../../../shared/models/goal.dart';
import '../domain/dashboard_repository.dart';
import '../data/dashboard_repository_impl.dart';

final localCacheServiceProvider = Provider<LocalCacheService>((ref) {
  return LocalCacheService();
});

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  final service = ConnectivityService();
  ref.onDispose(() => service.dispose());
  return service;
});

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  final cache = ref.watch(localCacheServiceProvider);
  final connectivity = ref.watch(connectivityServiceProvider);
  return DashboardRepositoryImpl(
    apiClient: client,
    localCache: cache,
    connectivity: connectivity,
  );
});

// Financial Overview AsyncNotifier
class OverviewNotifier extends AutoDisposeAsyncNotifier<FinancialOverview> {
  @override
  Future<FinancialOverview> build() async {
    final repo = ref.watch(dashboardRepositoryProvider);
    return await repo.getOverview();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(dashboardRepositoryProvider);
      return await repo.getOverview(forceRefresh: true);
    });
  }
}

final overviewNotifierProvider =
    AutoDisposeAsyncNotifierProvider<OverviewNotifier, FinancialOverview>(() {
  return OverviewNotifier();
});

// Anomalies Provider
final anomaliesProvider = AutoDisposeFutureProvider<List<Anomaly>>((ref) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  return await repo.getAnomalies();
});

// Health Score Provider
final healthScoreProvider = AutoDisposeFutureProvider<HealthScore>((ref) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  return await repo.getHealthScore();
});

// Family Provider for Forecast Horizons (7d, 30d, 90d)
final forecastFamilyProvider =
    AutoDisposeFutureProvider.family<Forecast, String>((ref, horizon) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  return await repo.getForecast(horizon: horizon);
});

// Cash Flow Provider
final cashFlowProvider = AutoDisposeFutureProvider<CashFlowProjection>((ref) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  return await repo.getCashFlowProjection();
});

// Goals Provider
final goalsProvider = AutoDisposeFutureProvider<List<Goal>>((ref) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  return await repo.getGoals();
});
