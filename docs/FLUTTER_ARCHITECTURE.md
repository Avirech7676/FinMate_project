# FinMate 2.0 Mobile: Flutter Architecture

## 1. Executive Summary

FinMate 2.0 Mobile (`flutter_app/`) is an enterprise-grade financial intelligence application built on Flutter and Dart. It operates as a client to the existing FinMate FastAPI backend without duplicating backend mathematical engines (Holt-Winters forecasting, 3-tier anomaly detection, explainable financial health scoring, and purchase simulation).

---

## 2. Architectural Layers

The application is structured according to Clean Architecture and Feature-Driven Development principles:

```
┌────────────────────────────────────────────────────────┐
│                   Presentation Layer                   │
│   - Material 3 Reactive UI (Screens & Widgets)          │
│   - CustomPainter 60 FPS Canvas Gauges                 │
│   - Riverpod Providers & AsyncNotifiers                │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│                      Domain Layer                      │
│   - Strongly Typed Models (Transaction, Forecast, etc)  │
│   - Abstract Repository Contracts                      │
│   - Typed Failure & Business Error Mappings            │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│                       Data Layer                       │
│   - RemoteDataSource: Centralized Dio Client           │
│   - LocalDataSource: SQLite Persistent Cache           │
│   - Secure Enclave: FlutterSecureStorage (JWTs)        │
│   - Offline Sync Queue for Mutations                   │
└───────────────────────────▲────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────┐
│                 Core Concurrency Layer                 │
│   - Persistent IsolateWorkerPool (SendPort/ReceivePort)│
│   - Off-Thread CSV Parsing & Sanitization Engine       │
│   - Off-Thread Financial Statistical Aggregation       │
└────────────────────────────────────────────────────────┘
```

---

## 3. Flutter Rendering Pipeline & UI Tree

Flutter utilizes three complementary trees to achieve high-performance rendering:

1. **Widget Tree**: Lightweight, immutable blueprints of the user interface created during the `build()` lifecycle.
2. **Element Tree**: Mutable bridge objects that manage the widget lifecycle, retain state, and orchestrate element reconciliation.
3. **Render Tree (`RenderObject`)**: Computes layout geometry (`layout()`), hit-testing (`hitTest()`), and hardware-accelerated painting (`paint()`) via the Skia/Impeller graphics engine.

In FinMate 2.0, expensive analytical graphics (such as the `HealthScoreGauge`) bypass complex nested widget hierarchies by directly implementing `CustomPainter`, achieving zero frame drops at a constant 60/120 FPS.

---

## 4. State Management with Riverpod

State management is powered by `flutter_riverpod`:

* **Unidirectional Data Flow**: User interactions invoke methods on `AsyncNotifier`s or `Notifier`s, which mutate immutable state and notify subscribed UI listeners.
* **Granular Rebuilds**: Widgets selectively subscribe to sub-states using `ref.watch()`.
* **Parameterized State**: Family providers (e.g., `forecastFamilyProvider('30d')`) isolate independent horizon state trees.
* **Automatic Lifecycle Disposal**: `AutoDispose` frees heap allocations when screens are unmounted.

---

## 5. Offline-First Read Architecture

The application adopts an offline-first caching strategy:
1. **Reads**: Data is requested from `ApiClient`. Upon network failure or offline detection, the repository immediately serves cached data from the local SQLite database alongside a visual `ConnectivityBanner`.
2. **Writes**: If an offline mutation occurs (e.g., creating a transaction), an optimistic entry is inserted into the UI and written to the `offline_sync_queue` table.
3. **Resumption**: When `ConnectivityService` detects an online transition, `syncOfflineQueue()` pushes pending items to FastAPI.
