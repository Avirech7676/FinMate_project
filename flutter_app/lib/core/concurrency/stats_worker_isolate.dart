import 'dart:isolate';
import 'dart:math' as math;
import 'task_contracts.dart';

/// Worker isolate implementation for CPU-heavy statistical aggregations and outlier metrics.
class StatsWorkerIsolate {
  StatsWorkerIsolate._();

  static Map<String, dynamic> process(WorkerTask task, SendPort progressPort) {
    final payload = task.payload as Map<String, dynamic>;
    final amounts = (payload['amounts'] as List<dynamic>)
        .map((e) => (e as num).toDouble())
        .toList();

    if (amounts.isEmpty) {
      return {
        'count': 0,
        'sum': 0.0,
        'mean': 0.0,
        'median': 0.0,
        'standardDeviation': 0.0,
        'min': 0.0,
        'max': 0.0,
        'iqr': 0.0,
        'outlierThreshold': 0.0,
      };
    }

    final n = amounts.length;
    final sum = amounts.reduce((a, b) => a + b);
    final mean = sum / n;

    // Report progress
    progressPort.send(
      WorkerProgress(
        taskId: task.taskId,
        percentage: 0.35,
        processedCount: (n * 0.35).toInt(),
        totalCount: n,
        statusMessage: 'Sorting and calculating distribution...',
      ),
    );

    // Sort for median and quartiles
    final sorted = List<double>.from(amounts)..sort();
    final median = n.isOdd ? sorted[n ~/ 2] : (sorted[n ~/ 2 - 1] + sorted[n ~/ 2]) / 2.0;

    // Variance & Standard Deviation
    double sumSquaredDiff = 0.0;
    for (final val in amounts) {
      final diff = val - mean;
      sumSquaredDiff += diff * diff;
    }
    final variance = sumSquaredDiff / n;
    final stdDev = math.sqrt(variance);

    // Quartiles & IQR
    final q1Index = (n * 0.25).floor();
    final q3Index = (n * 0.75).floor();
    final q1 = sorted[q1Index.clamp(0, n - 1)];
    final q3 = sorted[q3Index.clamp(0, n - 1)];
    final iqr = q3 - q1;
    final outlierUpperFence = q3 + 1.5 * iqr;

    // Find anomalies
    final anomalies = amounts.where((a) => a > outlierUpperFence).toList();

    progressPort.send(
      WorkerProgress(
        taskId: task.taskId,
        percentage: 1.0,
        processedCount: n,
        totalCount: n,
        statusMessage: 'Completed statistical computations.',
      ),
    );

    return {
      'count': n,
      'sum': sum,
      'mean': mean,
      'median': median,
      'variance': variance,
      'standardDeviation': stdDev,
      'min': sorted.first,
      'max': sorted.last,
      'q1': q1,
      'q3': q3,
      'iqr': iqr,
      'outlierThreshold': outlierUpperFence,
      'anomalyCount': anomalies.length,
    };
  }
}
