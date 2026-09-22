import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../auth/presentation/auth_providers.dart';
import '../../dashboard/presentation/dashboard_providers.dart';
import '../../../shared/models/transaction.dart';
import '../domain/transaction_repository.dart';
import '../data/transaction_repository_impl.dart';

final transactionRepositoryProvider = Provider<TransactionRepository>((ref) {
  final client = ref.watch(apiClientProvider);
  final cache = ref.watch(localCacheServiceProvider);
  final connectivity = ref.watch(connectivityServiceProvider);
  return TransactionRepositoryImpl(
    apiClient: client,
    localCache: cache,
    connectivity: connectivity,
  );
});

// Transaction Filter State Record
typedef TransactionFilter = ({
  String selectedCategory,
  String searchQuery,
  int page,
});

class TransactionListNotifier
    extends AutoDisposeFamilyAsyncNotifier<List<Transaction>, TransactionFilter> {
  @override
  Future<List<Transaction>> build(TransactionFilter arg) async {
    final repo = ref.watch(transactionRepositoryProvider);
    return await repo.getTransactions(
      page: arg.page,
      category: arg.selectedCategory == 'All' ? null : arg.selectedCategory,
      searchQuery: arg.searchQuery.isEmpty ? null : arg.searchQuery,
    );
  }

  Future<void> createTransaction({
    required double amount,
    required String category,
    required String description,
    required DateTime date,
    bool isIncome = false,
  }) async {
    final repo = ref.read(transactionRepositoryProvider);
    final newTx = await repo.createTransaction(
      amount: amount,
      category: category,
      description: description,
      date: date,
      isIncome: isIncome,
    );

    // Optimistically update current state
    state.whenData((current) {
      state = AsyncValue.data([newTx, ...current]);
    });
  }

  Future<void> deleteTransaction(String id) async {
    final repo = ref.read(transactionRepositoryProvider);
    await repo.deleteTransaction(id);

    state.whenData((current) {
      state = AsyncValue.data(current.where((t) => t.id != id).toList());
    });
  }
}

final transactionListNotifierProvider = AutoDisposeAsyncNotifierProviderFamily<
    TransactionListNotifier, List<Transaction>, TransactionFilter>(() {
  return TransactionListNotifier();
});
