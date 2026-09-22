import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/ai_message.dart';
import '../ai_providers.dart';

class AIChatScreen extends ConsumerStatefulWidget {
  const AIChatScreen({super.key});

  @override
  ConsumerState<AIChatScreen> createState() => _AIChatScreenState();
}

class _AIChatScreenState extends ConsumerState<AIChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage([String? presetText]) {
    final text = presetText ?? _textController.text;
    if (text.trim().isEmpty) return;

    ref.read(aiChatNotifierProvider.notifier).sendUserMessage(text);
    _textController.clear();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(aiChatNotifierProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.psychology_rounded, color: Color(0xFF818CF8)),
            SizedBox(width: 8),
            Text('AI Financial Advisor'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_sweep_rounded),
            tooltip: 'Clear History',
            onPressed: () => ref.read(aiChatNotifierProvider.notifier).clearHistory(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Live Tool Execution Status Indicator
          if (chatState.currentToolStatus != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: const Color(0xFF6366F1).withOpacity(0.15),
              child: Row(
                children: [
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Color(0xFF818CF8),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    chatState.currentToolStatus!,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF818CF8),
                    ),
                  ),
                ],
              ),
            ),

          // Messages List
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: chatState.messages.length,
              itemBuilder: (context, index) {
                final msg = chatState.messages[index];
                return _MessageBubble(
                  message: msg,
                  onActionTapped: (action) => _sendMessage(action),
                );
              },
            ),
          ),

          // Message Input Field
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: Color(0xFF1E293B),
              border: Border(top: BorderSide(color: Color(0xFF334155))),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                      decoration: const InputDecoration(
                        hintText: 'Ask FinMate AI Advisor...',
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.zero,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.send_rounded, color: Color(0xFF818CF8)),
                    onPressed: chatState.isLoading ? null : () => _sendMessage(),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final AIMessage message;
  final void Function(String action) onActionTapped;

  const _MessageBubble({
    required this.message,
    required this.onActionTapped,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == MessageSender.user;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.82,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isUser ? const Color(0xFF6366F1) : const Color(0xFF1E293B),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isUser ? 16 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 16),
              ),
              border: Border.all(
                color: isUser
                    ? const Color(0xFF6366F1)
                    : message.isError
                        ? const Color(0xFFEF4444)
                        : const Color(0xFF334155),
              ),
            ),
            child: Text(
              message.content,
              style: TextStyle(
                fontSize: 14,
                color: message.isError ? const Color(0xFFEF4444) : const Color(0xFFF8FAFC),
                height: 1.4,
              ),
            ),
          ),

          // Suggested Action Chips
          if (!isUser && message.suggestedActions != null) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: message.suggestedActions!.map((act) {
                return ActionChip(
                  label: Text(act, style: const TextStyle(fontSize: 11)),
                  backgroundColor: const Color(0xFF1E293B),
                  side: const BorderSide(color: Color(0xFF6366F1), width: 0.8),
                  onPressed: () => onActionTapped(act),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }
}
