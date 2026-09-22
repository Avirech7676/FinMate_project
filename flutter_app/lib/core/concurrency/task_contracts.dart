/// Strongly-typed contracts for Isolate thread communication.
/// Supports both one-shot request-response patterns and streaming progress reports.

enum TaskType {
  parseCsv,
  computeStatistics,
  filterDataset,
  generateReport,
  hashData,
}

/// Request envelope sent from UI isolate to worker isolate.
class WorkerTask {
  final String taskId;
  final TaskType type;
  final dynamic payload;

  const WorkerTask({
    required this.taskId,
    required this.type,
    required this.payload,
  });
}

/// Response envelope sent from worker isolate back to UI isolate.
class WorkerResponse {
  final String taskId;
  final bool isSuccess;
  final dynamic result;
  final String? errorMessage;
  final int executionTimeMs;

  const WorkerResponse({
    required this.taskId,
    required this.isSuccess,
    this.result,
    this.errorMessage,
    required this.executionTimeMs,
  });

  factory WorkerResponse.success(String taskId, dynamic result, int executionTimeMs) {
    return WorkerResponse(
      taskId: taskId,
      isSuccess: true,
      result: result,
      executionTimeMs: executionTimeMs,
    );
  }

  factory WorkerResponse.failure(String taskId, String error, int executionTimeMs) {
    return WorkerResponse(
      taskId: taskId,
      isSuccess: false,
      errorMessage: error,
      executionTimeMs: executionTimeMs,
    );
  }
}

/// Streaming progress report sent from worker isolate during long-running batch jobs.
class WorkerProgress {
  final String taskId;
  final double percentage; // 0.0 to 1.0
  final int processedCount;
  final int totalCount;
  final String? statusMessage;

  const WorkerProgress({
    required this.taskId,
    required this.percentage,
    required this.processedCount,
    required this.totalCount,
    this.statusMessage,
  });
}
