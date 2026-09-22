import 'dart:async';
import 'dart:isolate';
import 'dart:io' show Platform;
import 'task_contracts.dart';
import 'csv_worker_isolate.dart';
import 'stats_worker_isolate.dart';
import 'report_worker_isolate.dart';

/// Internal representation of an active long-lived worker isolate thread.
class _ActiveWorker {
  final int id;
  final Isolate isolate;
  final SendPort sendPort;
  final ReceivePort receivePort;
  bool isBusy = false;

  _ActiveWorker({
    required this.id,
    required this.isolate,
    required this.sendPort,
    required this.receivePort,
  });
}

/// A high-performance, persistent pool of background Dart Isolates.
///
/// Eliminates the cold-start overhead of creating/tearing down OS threads for every
/// CPU-bound job. Distributes compute tasks across background isolates using
/// round-robin scheduling and bidirectional port messaging.
class IsolateWorkerPool {
  final int poolSize;
  final List<_ActiveWorker> _workers = [];
  final Map<String, Completer<WorkerResponse>> _pendingTasks = {};
  final Map<String, StreamController<WorkerProgress>> _progressControllers = {};
  int _roundRobinIndex = 0;
  bool _isInitialized = false;

  IsolateWorkerPool({int? size})
      : poolSize = size ??
            (() {
              try {
                final cores = Platform.numberOfProcessors;
                return (cores > 1 ? cores - 1 : 1).clamp(2, 4);
              } catch (_) {
                return 2;
              }
            })();

  bool get isInitialized => _isInitialized;

  /// Initializes the pool by spawning isolates and establishing communication ports.
  Future<void> initialize() async {
    if (_isInitialized) return;

    for (int i = 0; i < poolSize; i++) {
      final worker = await _spawnWorker(i);
      _workers.add(worker);
    }
    _isInitialized = true;
  }

  Future<_ActiveWorker> _spawnWorker(int id) async {
    final handshakePort = ReceivePort();

    final isolate = await Isolate.spawn(
      _workerEntryPoint,
      handshakePort.sendPort,
      debugName: 'FinMateWorker-$id',
    );

    // Receive the worker's dedicated SendPort
    final workerSendPort = await handshakePort.first as SendPort;

    // Create a new port for regular message handling
    final workerReceivePort = ReceivePort();

    // Establish continuous bidirectional communication
    workerSendPort.send(workerReceivePort.sendPort);

    final activeWorker = _ActiveWorker(
      id: id,
      isolate: isolate,
      sendPort: workerSendPort,
      receivePort: workerReceivePort,
    );

    workerReceivePort.listen((message) {
      if (message is WorkerProgress) {
        _progressControllers[message.taskId]?.add(message);
      } else if (message is WorkerResponse) {
        activeWorker.isBusy = false;
        final completer = _pendingTasks.remove(message.taskId);
        completer?.complete(message);
        _progressControllers.remove(message.taskId)?.close();
      }
    });

    return activeWorker;
  }

  /// Dispatches a CPU-bound [WorkerTask] to an available isolate.
  /// Optional [onProgress] callback for receiving incremental streaming updates.
  Future<WorkerResponse> execute(
    WorkerTask task, {
    void Function(WorkerProgress progress)? onProgress,
  }) async {
    if (!_isInitialized) {
      await initialize();
    }

    final completer = Completer<WorkerResponse>();
    _pendingTasks[task.taskId] = completer;

    if (onProgress != null) {
      // ignore: close_sinks
      final controller = StreamController<WorkerProgress>.broadcast();
      _progressControllers[task.taskId] = controller;
      controller.stream.listen(onProgress);
    }

    // Select worker via round-robin
    final worker = _workers[_roundRobinIndex];
    _roundRobinIndex = (_roundRobinIndex + 1) % _workers.length;
    worker.isBusy = true;

    worker.sendPort.send(task);

    return completer.future;
  }

  /// Tears down all worker isolates and releases ports.
  void dispose() {
    for (final worker in _workers) {
      worker.receivePort.close();
      worker.isolate.kill(priority: Isolate.immediate);
    }
    _workers.clear();
    for (final controller in _progressControllers.values) {
      controller.close();
    }
    _progressControllers.clear();
    _pendingTasks.clear();
    _isInitialized = false;
  }
}

/// Entry point executed inside the separate memory heap of the spawned isolate.
void _workerEntryPoint(SendPort initialReplyTo) {
  final isolateReceivePort = ReceivePort();
  initialReplyTo.send(isolateReceivePort.sendPort);

  SendPort? mainIsolatePort;

  isolateReceivePort.listen((message) {
    if (message is SendPort) {
      mainIsolatePort = message;
    } else if (message is WorkerTask && mainIsolatePort != null) {
      _handleTask(message, mainIsolatePort!);
    }
  });
}

/// Executes task according to type and emits progress/results back across the port.
void _handleTask(WorkerTask task, SendPort replyPort) {
  final stopwatch = Stopwatch()..start();

  try {
    dynamic result;

    switch (task.type) {
      case TaskType.parseCsv:
        result = CsvWorkerIsolate.process(task, replyPort);
        break;
      case TaskType.computeStatistics:
        result = StatsWorkerIsolate.process(task, replyPort);
        break;
      case TaskType.generateReport:
        result = ReportWorkerIsolate.process(task, replyPort);
        break;
      case TaskType.filterDataset:
        result = _filterDatasetInternal(task.payload as Map<String, dynamic>);
        break;
      case TaskType.hashData:
        result = task.payload.toString().hashCode;
        break;
    }

    stopwatch.stop();
    replyPort.send(
      WorkerResponse.success(task.taskId, result, stopwatch.elapsedMilliseconds),
    );
  } catch (e, stack) {
    stopwatch.stop();
    replyPort.send(
      WorkerResponse.failure(
        task.taskId,
        'Worker Isolate Error: $e\n$stack',
        stopwatch.elapsedMilliseconds,
      ),
    );
  }
}

List<Map<String, dynamic>> _filterDatasetInternal(Map<String, dynamic> payload) {
  final items = payload['items'] as List<dynamic>;
  final query = (payload['query'] as String? ?? '').toLowerCase();
  final category = payload['category'] as String?;
  final minAmount = (payload['minAmount'] as num?)?.toDouble();
  final maxAmount = (payload['maxAmount'] as num?)?.toDouble();

  return items.whereType<Map<String, dynamic>>().where((item) {
    if (category != null && category != 'All' && item['category'] != category) {
      return false;
    }
    final amount = (item['amount'] as num?)?.toDouble() ?? 0.0;
    if (minAmount != null && amount < minAmount) return false;
    if (maxAmount != null && amount > maxAmount) return false;

    if (query.isNotEmpty) {
      final desc = (item['description'] as String? ?? '').toLowerCase();
      final cat = (item['category'] as String? ?? '').toLowerCase();
      if (!desc.contains(query) && !cat.contains(query)) return false;
    }
    return true;
  }).toList();
}
