import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../shared/models/simulation_result.dart';
import '../domain/simulation_repository.dart';

class SimulationRepositoryImpl implements SimulationRepository {
  final ApiClient _apiClient;

  SimulationRepositoryImpl({required ApiClient apiClient}) : _apiClient = apiClient;

  @override
  Future<SimulationResult> simulatePurchase({
    required double amount,
    required String category,
    required String description,
  }) async {
    final response = await _apiClient.post(
      ApiConstants.simulatePurchase,
      data: {
        'amount': amount,
        'category': category,
        'description': description,
      },
    );

    return SimulationResult.fromJson(response as Map<String, dynamic>);
  }
}
