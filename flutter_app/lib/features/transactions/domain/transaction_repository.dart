import '../../../shared/models/transaction.dart';

abstract class TransactionRepository {
  Future<List<Transaction>> getTransactions({
    int page = 1,
    int pageSize = 25,
    String? category,
    String? searchQuery,
    DateTime? startDate,
    DateTime? endDate,
    bool forceRefresh = false,
  });

  Future<Transaction> createTransaction({
    required double amount,
    required String category,
    required String description,
    required DateTime date,
    bool isIncome = false,
    bool isRecurring = false,
  });

  Future<void> deleteTransaction(String id);

  Future<void> syncOfflineQueue();
}
