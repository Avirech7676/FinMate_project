import '../../../shared/models/ai_message.dart';

abstract class AIRepository {
  Future<AIMessage> sendMessage({
    required String message,
    List<Map<String, String>>? conversationHistory,
    void Function(String toolStatus)? onToolStatus,
  });
}
