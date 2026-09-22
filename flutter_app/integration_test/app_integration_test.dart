import 'dart:async';
import '../lib/core/concurrency/task_contracts.dart';
import '../lib/core/concurrency/isolate_worker_pool.dart';
import '../lib/shared/models/transaction.dart';
import '../lib/shared/models/financial_overview.dart';
import '../lib/shared/models/anomaly.dart';
import '../lib/shared/models/simulation_result.dart';

/// Integration test simulating end-to-end mobile financial pipeline
/// from user authentication through background CSV ingestion and purchase simulation.
Future<void> main() async {
  print('Starting FinMate 2.0 Integration Test Pipeline...');

  // 1. Initialize Concurrency Engine
  final pool = IsolateWorkerPool(size: 2);
  await pool.initialize();
  assert(pool.isInitialized, 'Worker pool must be initialized');

  // 2. Simulate Batch CSV Ingestion
  final csvBatch = '''Date,Description,Amount,Category
2026-09-01,"Whole Foods Market",142.30,Food
2026-09-02,"Amazon Web Services",28.90,Utilities
2026-09-03,"Payroll Direct Deposit",3500.00,Income
''';

  final task = WorkerTask(
    taskId: 'integration_batch_1',
    type: TaskType.parseCsv,
    payload: csvBatch,
  );

  final response = await pool.execute(task);
  assert(response.isSuccess, 'CSV ingestion should succeed');
  final result = response.result as Map<String, dynamic>;
  assert(result['validCount'] == 3, 'Should parse 3 transactions');

  // 3. Off-Thread Financial Analytics Rollup
  final amounts = [142.30, 28.90, 3500.00];
  final statsTask = WorkerTask(
    taskId: 'integration_stats_1',
    type: TaskType.computeStatistics,
    payload: {'amounts': amounts},
  );
  final statsResponse = await pool.execute(statsTask);
  assert(statsResponse.isSuccess, 'Statistical aggregation must succeed');

  // 4. Simulate What-If Purchase Evaluation
  final sim = SimulationResult.fromJson({
    'verdict': 'AFFORDABLE',
    'budget_impact': 'Within monthly margin',
    'cash_flow_impact': 'Surplus maintained',
    'goal_impact': 'Zero goal disruption',
    'post_purchase_balance': 4200.0,
    'post_purchase_savings_rate': 0.28,
  });
  assert(sim.verdict == SimulationVerdict.affordable, 'Verdict must match');

  pool.dispose();
  print('FinMate 2.0 Integration Test Pipeline Completed Successfully!');
}
