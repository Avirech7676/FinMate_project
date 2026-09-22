import '../../../shared/models/financial_overview.dart';
import '../../../shared/models/anomaly.dart';
import '../../../shared/models/forecast.dart';
import '../../../shared/models/health_score.dart';
import '../../../shared/models/cash_flow_projection.dart';
import '../../../shared/models/goal.dart';

abstract class DashboardRepository {
  Future<FinancialOverview> getOverview({bool forceRefresh = false});
  Future<List<Anomaly>> getAnomalies();
  Future<Forecast> getForecast({String horizon = '30d'});
  Future<HealthScore> getHealthScore();
  Future<CashFlowProjection> getCashFlowProjection();
  Future<List<Goal>> getGoals();
}
