import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/presentation/auth_providers.dart';
import '../../../shared/models/ai_message.dart';
import '../domain/ai_repository.dart';
import '../data/ai_repository_impl.dart';

final aiRepositoryProvider = Provider<AIRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  return AIRepositoryImpl(apiClient: client);
});

typedef AIChatState = ({
  List<AIMessage> messages,
  bool isLoading,
  String? currentToolStatus,
  String? errorMessage,
});

class AIChatNotifier extends AutoDisposeNotifier<AIChatState> {
  @override
  AIChatState build() {
    return (
      messages: [
        AIMessage.assistant(
          'Hello! I am your FinMate AI Financial Advisor. I can analyze your spending anomalies, evaluate budget pacing, or simulate purchases.',
          actions: ['Analyze this month\'s anomalies', 'Review cash flow risk', 'Am I on track for my savings goal?'],
        ),
      ],
      isLoading: false,
      currentToolStatus: null,
      errorMessage: null,
    );
  }

  Future<void> sendUserMessage(String text) async {
    if (text.trim().isEmpty) return;

    final userMsg = AIMessage.user(text.trim());
    state = (
      messages: [...state.messages, userMsg],
      isLoading: true,
      currentToolStatus: 'Consulting FinMate Guardrails...',
      errorMessage: null,
    );

    try {
      final repo = ref.read(aiRepositoryProvider);
      final history = state.messages
          .where((m) => m.sender != MessageSender.system)
          .map((m) => {
                'role': m.sender == MessageSender.user ? 'user' : 'assistant',
                'content': m.content,
              })
          .toList();

      final reply = await repo.sendMessage(
        message: text.trim(),
        conversationHistory: history,
        onToolStatus: (status) {
          state = (
            messages: state.messages,
            isLoading: true,
            currentToolStatus: status,
            errorMessage: null,
          );
        },
      );

      state = (
        messages: [...state.messages, reply],
        isLoading: false,
        currentToolStatus: null,
        errorMessage: null,
      );
    } catch (e) {
      state = (
        messages: [
          ...state.messages,
          AIMessage.error('Unable to complete request. Please verify your connection and retry.'),
        ],
        isLoading: false,
        currentToolStatus: null,
        errorMessage: e.toString(),
      );
    }
  }

  void clearHistory() {
    state = (
      messages: [
        AIMessage.assistant('Conversation reset. How can I help you today?'),
      ],
      isLoading: false,
      currentToolStatus: null,
      errorMessage: null,
    );
  }
}

final aiChatNotifierProvider =
    AutoDisposeNotifierProvider<AIChatNotifier, AIChatState>(() {
  return AIChatNotifier();
});
