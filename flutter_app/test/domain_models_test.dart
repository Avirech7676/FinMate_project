import 'package:test/test.dart';
import '../lib/shared/models/transaction.dart';
import '../lib/shared/models/financial_overview.dart';
import '../lib/shared/models/anomaly.dart';
import '../lib/shared/models/forecast.dart';
import '../lib/shared/models/health_score.dart';
import '../lib/shared/models/simulation_result.dart';

void main() {
  group('FinMate 2.0 Strongly Typed Domain Models', () {
    test('Transaction parses valid JSON and round-trips correctly', () {
      final json = {
        'id': 'tx_123',
        'amount': 45.99,
        'category': 'Food',
        'description': 'Trader Joe\'s',
        'date': '2026-09-22T14:30:00.000Z',
        'is_income': false,
        'is_recurring': false,
      };

      final tx = Transaction.fromJson(json);
      expect(tx.id, equals('tx_123'));
      expect(tx.amount, equals(45.99));
      expect(tx.category, equals('Food'));
      expect(tx.isIncome, isFalse);

      final out = tx.toJson();
      expect(out['id'], equals('tx_123'));
      expect(out['amount'], equals(45.99));
    });

    test('FinancialOverview computes net savings and rates cleanly', () {
      final json = {
        'total_income': 6000.0,
        'total_expenses': 4200.0,
        'net_savings': 1800.0,
        'savings_rate': 0.30,
        'transaction_count': 42,
        'health_score': 84.5,
        'cash_flow_risk': 'LOW',
        'category_breakdown': {'Food': 800.0, 'Housing': 2000.0},
      };

      final overview = FinancialOverview.fromJson(json);
      expect(overview.totalIncome, equals(6000.0));
      expect(overview.totalExpenses, equals(4200.0));
      expect(overview.netSavings, equals(1800.0));
      expect(overview.savingsRate, equals(0.30));
      expect(overview.healthScore, equals(84.5));
      expect(overview.cashFlowRisk, equals('LOW'));
    });

    test('Anomaly maps detection layers and severity levels accurately', () {
      final json = {
        'id': 'anom_1',
        'transaction_id': 'tx_99',
        'description': 'Luxury Watch',
        'amount': 2500.0,
        'category': 'Shopping',
        'reason': 'Amount exceeds 3-sigma historical baseline',
        'severity': 'critical',
        'layer': 'statistical',
        'score': 0.96,
      };

      final anom = Anomaly.fromJson(json);
      expect(anom.severity, equals(AnomalySeverity.critical));
      expect(anom.layer, equals(AnomalyLayer.statistical));
      expect(anom.score, equals(0.96));
    });

    test('SimulationResult maps AFFORDABLE, CAUTION, and UNRECOMMENDED verdicts', () {
      final affordableJson = {
        'verdict': 'AFFORDABLE',
        'budget_impact': 'Within limits',
        'cash_flow_impact': 'Positive balance maintained',
        'goal_impact': 'No goals impacted',
        'post_purchase_balance': 4500.0,
        'post_purchase_savings_rate': 0.28,
        'explanation': 'Purchase fits comfortable discretionary budget.',
      };

      final affordable = SimulationResult.fromJson(affordableJson);
      expect(affordable.verdict, equals(SimulationVerdict.affordable));

      final caution = SimulationResult.fromJson({'verdict': 'PROCEED_WITH_CAUTION'});
      expect(caution.verdict, equals(SimulationVerdict.proceedWithCaution));

      final unrec = SimulationResult.fromJson({'verdict': 'UNRECOMMENDED'});
      expect(unrec.verdict, equals(SimulationVerdict.unrecommended));
    });

    test('Forecast deserializes discrete projection points and metadata', () {
      final json = {
        'horizon': '30d',
        'projected_total': 3450.0,
        'model_name': 'Holt-Winters Multiplicative',
        'points': [
          {'date': '2026-09-23', 'predicted': 115.0},
          {'date': '2026-09-24', 'predicted': 120.0},
        ],
      };

      final forecast = Forecast.fromJson(json);
      expect(forecast.horizon, equals('30d'));
      expect(forecast.projectedTotal, equals(3450.0));
      expect(forecast.points.length, equals(2));
      expect(forecast.points.first.predictedAmount, equals(115.0));
    });
  });
}
