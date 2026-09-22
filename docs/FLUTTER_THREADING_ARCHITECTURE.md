# FinMate 2.0 — Flutter & Dart Threading Architecture Guide

**Platform**: FinMate 2.0 Mobile Companion (`finmate_mobile`)  
**Technologies**: Flutter, Dart 3.x, Isolates, Concurrency Worker Pools, CustomPainter, Clean Architecture  
**Scope**: In-depth Dart threading, background worker pools, non-blocking UI rendering, and enterprise cross-platform mobile design.

---

## 1. Concurrency Architecture Overview

In Flutter and Dart, the execution model differs fundamentally from multi-threaded environments like Java or C++:
* **Single-Threaded Event Loop by Default**: Every Flutter app runs on a primary UI thread governed by an **Event Loop**. This loop processes microtasks, user inputs, timer callbacks, animations, and render pipeline updates (Layout $\to$ Paint $\to$ Composite) at 60 or 120 frames per second (16.6ms / 8.3ms per frame).
* **Frame Drop / Jank Risk**: If a CPU-bound operation (e.g. parsing a 5MB CSV with 20,000 transactions, computing standard deviations, or performing SHA-256 hashing) runs on the main thread and exceeds 16ms, the UI drops frames, causing noticeable stutter and unresponsiveness.
* **Isolates as True Concurrency**: Dart provides **Isolates**—independent execution threads with their own dedicated, isolated memory heaps. Because isolates never share memory, there are **no race conditions, no locks, and no mutexes**. All communication occurs via asynchronous message passing across `SendPort` and `ReceivePort`.

---

## 2. FinMate Isolate Concurrency Subsystem

FinMate 2.0 implements two distinct Dart concurrency patterns:

### 2.1 The Persistent Worker Pool (`IsolateWorkerPool`)
For repetitive, high-frequency, or streaming operations, continuously creating and destroying isolates incurs a non-trivial cold-start spawn cost (~20–40ms). FinMate solves this with `IsolateWorkerPool`:

```
┌────────────────────────────────────────────────────────┐
│                   Main UI Thread                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           IsolateWorkerPool (Singleton)          │  │
│  │  - Round-robin Dispatcher                        │  │
│  │  - Pending Task Map: Map<taskId, Completer>      │  │
│  │  - Progress Stream Map: Map<taskId, StreamCtrl>  │  │
│  └──────────────────────┬───────────────────────────┘  │
└─────────────────────────┼──────────────────────────────┘
                          │ Bidirectional Ports
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────┐
│     Worker Isolate 0    │ │     Worker Isolate 1    │
│  - Dedicated Heap       │ │  - Dedicated Heap       │
│  - CsvWorkerIsolate     │ │  - CsvWorkerIsolate     │
│  - StatsWorkerIsolate   │ │  - StatsWorkerIsolate   │
│  - Port Handshake Loop  │ │  - Port Handshake Loop  │
└─────────────────────────┘ └─────────────────────────┘
```

#### Handshake Protocol
1. **Spawn**: The main thread spawns a worker isolate via `Isolate.spawn`, passing an initialization payload containing `parentSendPort`.
2. **Step 1**: The worker creates its own `ReceivePort` and sends its `SendPort` back to the parent.
3. **Step 2**: The parent creates a dedicated response port and sends its `SendPort` to the worker.
4. **Task Dispatch**: Tasks (`WorkerTask`) are posted to the worker's `SendPort`.
5. **Streaming Updates**: Long-running tasks emit `WorkerProgress` messages to the parent's response port, which pipes them to a reactive Flutter `StreamBuilder` or `LinearProgressIndicator`.
6. **Completion**: Upon finishing, the worker emits `WorkerResponse` containing execution microsecond benchmarks. The parent completes the matching `Completer<WorkerResponse>`.

---

### 2.2 Ephemeral Concurrency (`Isolate.run`)
For one-off, discrete compute operations where streaming progress is not required, FinMate uses Dart's `Isolate.run`:
```dart
static Future<String> generateTransactionFingerprint({
  required double amount,
  required String date,
  required String description,
}) async {
  return Isolate.run<String>(() {
    final raw = '${amount.toStringAsFixed(2)}|$date|${description.trim().toLowerCase()}';
    final bytes = utf8.encode(raw);
    return sha256.convert(bytes).toString();
  });
}
```
`Isolate.run` spawns an isolate, transfers the closure, computes the return value, and automatically terminates the isolate.

---

## 3. Implemented Worker Workloads

### 3.1 Streaming CSV Ingestion (`CsvWorkerIsolate`)
- **Location**: `lib/core/threading/csv_worker_isolate.dart`
- **Responsibilities**:
  1. Parses raw multi-line CSV with double-quote escape handling.
  2. Detects flexible header schemas (`Date`, `Amount`, `Description`, `Category`).
  3. Formats dates and strips extraneous currency symbols (`$`, `€`, `₹`).
  4. Deduplicates identical records using compound date-amount-description keys.
  5. Emits `WorkerProgress` events every 250 rows to keep the UI informed in real-time.

### 3.2 Real-Time Statistical Modeling & Anomalies (`StatsWorkerIsolate`)
- **Location**: `lib/core/threading/stats_worker_isolate.dart`
- **Responsibilities**:
  1. Computes financial metrics: Mean, Median, Variance, Standard Deviation.
  2. Calculates 25th percentile (Q1), 75th percentile (Q3), and Interquartile Range (IQR).
  3. Derives the Tukey upper fence ($Q3 + 1.5 \times IQR$).
  4. Flags statistical outliers and computes anomaly severity scores ($1.0 - 10.0$).
  5. Aggregates category spending totals.

---

## 4. In-Depth Flutter Concepts

### 4.1 Custom RenderObject Painting (`CustomPainter`)
- **Widget**: `HealthScoreGauge` (`lib/presentation/widgets/health_score_gauge.dart`)
- **Implementation**:
  - Leverages Flutter's canvas low-level drawing commands (`drawArc`, `drawCircle`, `TextPainter`).
  - Employs a multi-stop `SweepGradient` with neon cyan, emerald, and violet colors.
  - Driven by an `AnimationController` and `CurvedAnimation(Curves.easeOutCubic)` ensuring a butter-smooth 60fps radial needle and score counter.
  - Implements `shouldRepaint` optimizations to avoid redundant render tree passes.

### 4.2 State Management Architecture
- Clean separation between **Domain Entities** (`Transaction`, `HealthScore`), **Data Repositories** (`TransactionRepositoryImpl`), and **Presentation Providers** (`AuthProvider`, `TransactionProvider`, `DashboardProvider`).
- Uses reactive `ChangeNotifier` and `AnimatedBuilder` / `Listenable.merge` to rebuild only the UI sub-trees that change, avoiding expensive full-widget rebuilds.

---

## 5. Directory Structure of `finmate_mobile`

```
finmate_mobile/
├── pubspec.yaml                          # Flutter & Dart dependencies
├── analysis_options.yaml                 # Strict type safety and lint rules
├── lib/
│   ├── main.dart                         # Entrypoint, DI setup, and router
│   ├── core/
│   │   ├── config/api_constants.dart     # Backend URLs & endpoints
│   │   ├── network/api_client.dart       # HTTP client with JWT interceptor
│   │   ├── network/exceptions.dart       # Typed network exceptions
│   │   ├── theme/app_theme.dart          # Fintech dark theme tokens
│   │   └── threading/                    # CONCURRENCY SUBSYSTEM
│   │       ├── task_contracts.dart       # Task & response contracts
│   │       ├── isolate_worker_pool.dart  # Multi-threaded persistent isolate pool
│   │       ├── csv_worker_isolate.dart   # Streaming CSV parser in isolate
│   │       ├── stats_worker_isolate.dart # Stats & anomaly engine in isolate
│   │       └── background_crypto.dart    # Isolate.run SHA-256 hashing
│   ├── domain/
│   │   ├── models/                       # Immutable domain entities
│   │   └── repositories/                 # Repository abstractions
│   ├── data/
│   │   └── repositories/                 # REST API implementations
│   └── presentation/
│       ├── providers/                    # Reactive state notifiers
│       ├── widgets/                      # CustomPainter & UI components
│       └── screens/                      # Mobile screens
└── test/
    ├── isolate_worker_test.dart          # Threading & pool unit tests
    ├── csv_isolate_test.dart             # CSV isolate unit tests
    └── transaction_model_test.dart       # Model serialization tests
```

---

## 6. Verification & Test Execution

The codebase includes automated unit tests covering domain models, isolate message passing, CSV parsing, and statistical calculations:

```bash
cd finmate_mobile
flutter test
```
All business logic, isolate communication protocols, and parsing routines are verified and production-ready.
