import '../../../shared/models/simulation_result.dart';

abstract class SimulationRepository {
  Future<SimulationResult> simulatePurchase({
    required double amount,
    required String category,
    required String description,
  });
}
