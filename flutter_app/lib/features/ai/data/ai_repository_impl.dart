import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../shared/models/ai_message.dart';
import '../domain/ai_repository.dart';

class AIRepositoryImpl implements AIRepository {
  final ApiClient _apiClient;

  AIRepositoryImpl({required ApiClient apiClient}) : _apiClient = apiClient;

  @override
  Future<AIMessage> sendMessage({
    required String message,
    List<Map<String, String>>? conversationHistory,
    void Function(String toolStatus)? onToolStatus,
  }) async {
    // Notify presentation layer of tool activity sequence
    onToolStatus?.call('Analyzing context & financial guardrails...');

    final response = await _apiClient.post(
      ApiConstants.aiChat,
      data: {
        'message': message,
        if (conversationHistory != null) 'history': conversationHistory,
      },
    );

    final responseData = response as Map<String, dynamic>;
    final reply = responseData['response'] as String? ??
        responseData['reply'] as String? ??
        'Financial analysis completed.';

    final rawActions = responseData['suggested_actions'] as List<dynamic>? ?? [];
    final actions = rawActions.map((e) => e.toString()).toList();

    return AIMessage.assistant(reply, actions: actions.isNotEmpty ? actions : null);
  }
}
