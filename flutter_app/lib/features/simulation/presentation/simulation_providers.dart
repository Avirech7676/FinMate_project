import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/presentation/auth_providers.dart';
import '../../../shared/models/simulation_result.dart';
import '../domain/simulation_repository.dart';
import '../data/simulation_repository_impl.dart';

final simulationRepositoryProvider = Provider<SimulationRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return SimulationRepositoryImpl(apiClient: client);
});

class SimulationNotifier extends AutoDisposeAsyncNotifier<SimulationResult?> {
  @override
  Future<SimulationResult?> build() async => null;

  Future<void> runSimulation({
    required double amount,
    required String category,
    required String description,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(simulationRepositoryProvider);
      return await repo.simulatePurchase(
        amount: amount,
        category: category,
        description: description,
      );
    });
  }

  void reset() {
    state = const AsyncValue.data(null);
  }
}

final simulationNotifierProvider =
    AutoDisposeAsyncNotifierProvider<SimulationNotifier, SimulationResult?>(() {
  return SimulationNotifier();
});
