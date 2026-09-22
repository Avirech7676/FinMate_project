import 'dart:isolate';
import 'task_contracts.dart';
import 'isolate_worker_pool.dart';

/// Facade for concurrency operations across FinMate 2.0.
/// Provides access to both the persistent worker pool and one-off `Isolate.run` workers.
class ComputeRunner {
  static final IsolateWorkerPool pool = IsolateWorkerPool();

  /// Executes a CPU-bound closure inside an ephemeral isolate via [Isolate.run].
  /// Ideal for small-to-medium non-recurrent tasks (e.g., fast hashing, small JSON transformation).
  static Future<R> runEphemeral<R>(R Function() computation) {
    return Isolate.run<R>(computation);
  }

  /// Dispatches an expensive batch operation to the persistent [IsolateWorkerPool] with
  /// streaming progress updates.
  static Future<WorkerResponse> runPooled(
    WorkerTask task, {
    void Function(WorkerProgress progress)? onProgress,
  }) {
    return pool.execute(task, onProgress: onProgress);
  }
}
