enum MessageSender { user, assistant, system }

/// Model representing a chat turn in the FinMate AI Financial Advisor.
class AIMessage {
  final String id;
  final MessageSender sender;
  final String content;
  final DateTime timestamp;
  final String? activeToolStatus; // e.g. "Fetching spending data...", "Analyzing anomalies..."
  final bool isError;
  final List<String>? suggestedActions;

  const AIMessage({
    required this.id,
    required this.sender,
    required this.content,
    required this.timestamp,
    this.activeToolStatus,
    this.isError = false,
    this.suggestedActions,
  });

  factory AIMessage.user(String content) {
    return AIMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      sender: MessageSender.user,
      content: content,
      timestamp: DateTime.now(),
    );
  }

  factory AIMessage.assistant(String content, {List<String>? actions}) {
    return AIMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      sender: MessageSender.assistant,
      content: content,
      timestamp: DateTime.now(),
      suggestedActions: actions,
    );
  }

  factory AIMessage.toolExecution(String status) {
    return AIMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      sender: MessageSender.system,
      content: '',
      timestamp: DateTime.now(),
      activeToolStatus: status,
    );
  }

  factory AIMessage.error(String errorMessage) {
    return AIMessage(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      sender: MessageSender.assistant,
      content: errorMessage,
      timestamp: DateTime.now(),
      isError: true,
    );
  }
}
