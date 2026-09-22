# FinMate 2.0 Mobile: Testing Strategy & Verification

## 1. Testing Pyramid

FinMate 2.0 Mobile implements a 3-tier testing strategy:

1. **Unit Tests (`test/`)**:
   - Concurrency & Isolate Workers (`test/concurrency_isolate_test.dart`)
   - Domain Model Serialization & JSON Validation (`test/domain_models_test.dart`)
   - Error & Exception Mapping (`test/error_mapping_test.dart`)
   - Formatters & Input Validators (`test/formatters_validators_test.dart`)
2. **Widget Tests**:
   - CustomPainter radial gauge rendering
   - MetricCard display & reactive UI bindings
   - Dismissible transaction list interactions
3. **Integration & Concurrency Benchmarks**:
   - UI responsiveness validation under 10,000 synthetic transaction records.

---

## 2. Running Test Suites

Execute all mobile tests using the Dart test runner:

```bash
cd flutter_app
dart test
```

Or when developing with the Flutter toolchain:

```bash
flutter test
```
