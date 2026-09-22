# FinMate 2.0 Mobile: Dart Engineering Guide

## 1. Modern Dart Language Features

The FinMate 2.0 mobile client leverages modern Dart 3 features across all architectural layers.

### 1.1 Sound Null Safety
* All types are non-nullable by default.
* Explicit nullability (`T?`) is restricted to optional fields (e.g., `String? anomalyFlag`, `DateTime? updatedAt`).
* Force unwrap operators (`!`) are avoided in favor of pattern matching or null-coalescing defaults (`??`).

### 1.2 Sealed Class Hierarchies
Sealed classes enforce exhaustive compile-time pattern matching for domain error handling:

```dart
sealed class Failure {
  final String message;
  const Failure(this.message);
}

class NetworkFailure extends Failure { ... }
class AuthenticationFailure extends Failure { ... }
class ValidationFailure extends Failure { ... }
```

When matching against `Failure`, the Dart compiler guarantees all branches are handled without requiring a fragile `default` fallback.

### 1.3 Records & Pattern Matching
Records allow lightweight grouping of parameters and filter states without boilerplate data classes:

```dart
typedef TransactionFilter = ({
  String selectedCategory,
  String searchQuery,
  int page,
});
```

Pattern matching enables succinct enum mapping:

```dart
final severity = switch (sevStr) {
  'low' => AnomalySeverity.low,
  'high' => AnomalySeverity.high,
  'critical' => AnomalySeverity.critical,
  _ => AnomalySeverity.medium,
};
```

---

## 2. Asynchronous Programming: Futures vs Streams vs Isolates

* **`Future`**: Represents a single deferred value. Used for asynchronous network I/O (`Dio.get`), database reads, and file writes.
* **`Stream`**: Represents a continuous sequence of asynchronous events. Used for `ConnectivityService` status broadcasts and `WorkerProgress` updates.
* **`Isolate`**: Dedicated OS-level thread with an independent memory heap. Used exclusively for CPU-intensive calculations (CSV parsing, statistics computation, report preparation) to guarantee zero UI jank.

---

## 3. Immutability & Clean Architecture

Domain models implement strict immutability:
* All class fields are declared `final`.
* State mutations are performed via explicit `copyWith(...)` methods.
* Prevents unpredictable side-effects in Riverpod reactive state subscriptions.
