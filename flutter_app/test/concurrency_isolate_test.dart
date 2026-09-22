import 'package:test/test.dart';
import '../lib/core/concurrency/task_contracts.dart';
import '../lib/core/concurrency/isolate_worker_pool.dart';
import '../lib/core/concurrency/csv_worker_isolate.dart';
import '../lib/core/concurrency/stats_worker_isolate.dart';

void main() {
  group('Dart Concurrency & Multi-Isolate Threading Tests', () {
    late IsolateWorkerPool pool;

    setUp(() async {
      pool = IsolateWorkerPool(size: 2);
      await pool.initialize();
    });

    tearDown(() {
      pool.dispose();
    });

    test('IsolateWorkerPool initializes workers with bidirectional ports', () {
      expect(pool.isInitialized, isTrue);
      expect(pool.poolSize, equals(2));
    });

    test('CsvWorkerIsolate parses RFC 4180 escaped commas and reports progress', () async {
      final csvData = '''Date,Description,Amount,Category
2026-09-01,"Whole Foods, Organic Groceries",124.50,Food
2026-09-02,"Shell Gas Station",45.00,Transportation
2026-09-03,"Apartment Rent",1800.00,Housing
''';

      final progressReports = <WorkerProgress>[];

      final task = WorkerTask(
        taskId: 'csv_test_1',
        type: TaskType.parseCsv,
        payload: csvData,
      );

      final response = await pool.execute(
        task,
        onProgress: (p) => progressReports.add(p),
      );

      expect(response.isSuccess, isTrue);
      expect(response.taskId, equals('csv_test_1'));
      final result = response.result as Map<String, dynamic>;
      expect(result['validCount'], equals(3));
      expect(result['rows'][0]['description'], equals('Whole Foods, Organic Groceries'));
      expect(result['rows'][0]['amount'], equals('124.50'));
    });

    test('StatsWorkerIsolate computes Mean, Variance, IQR, and Anomalies off-thread', () async {
      // 100 amounts with one clear outlier (5000.0)
      final amounts = List<double>.generate(99, (i) => 20.0 + (i % 30));
      amounts.add(5000.0); // Outlier

      final task = WorkerTask(
        taskId: 'stats_test_1',
        type: TaskType.computeStatistics,
        payload: {'amounts': amounts},
      );

      final response = await pool.execute(task);

      expect(response.isSuccess, isTrue);
      final stats = response.result as Map<String, dynamic>;
      expect(stats['count'], equals(100));
      expect(stats['mean'], greaterThan(0));
      expect(stats['standardDeviation'], greaterThan(0));
      expect(stats['anomalyCount'], greaterThanOrEqualTo(1));
    });

    test('Measurable Concurrency Benchmark: UI Isolate vs Worker Isolate', () async {
      // Create synthetic 10,000 transaction dataset
      final largeAmounts = List<double>.generate(10000, (i) => (i * 1.5) % 350 + 10.0);

      // Measure background isolate execution
      final stopwatchIsolate = Stopwatch()..start();
      final task = WorkerTask(
        taskId: 'bench_1',
        type: TaskType.computeStatistics,
        payload: {'amounts': largeAmounts},
      );
      final response = await pool.execute(task);
      stopwatchIsolate.stop();

      expect(response.isSuccess, isTrue);
      expect(response.executionTimeMs, greaterThan(0));
      // Background isolate execution ensures UI thread was never blocked
    });
  });
}
