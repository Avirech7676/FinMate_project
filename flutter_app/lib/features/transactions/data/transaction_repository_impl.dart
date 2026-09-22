import '../../../core/network/api_client.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/storage/local_cache_service.dart';
import '../../../core/network/connectivity_service.dart';
import '../../../core/errors/exceptions.dart';
import '../../../shared/models/transaction.dart';
import '../domain/transaction_repository.dart';

class TransactionRepositoryImpl implements TransactionRepository {
  final ApiClient _apiClient;
  final LocalCacheService _localCache;
  final ConnectivityService _connectivity;

  TransactionRepositoryImpl({
    required ApiClient apiClient,
    required LocalCacheService localCache,
    required ConnectivityService connectivity,
  })  : _apiClient = apiClient,
        _localCache = localCache,
        _connectivity = connectivity;

  @override
  Future<List<Transaction>> getTransactions({
    int page = 1,
    int pageSize = 25,
    String? category,
    String? searchQuery,
    DateTime? startDate,
    DateTime? endDate,
    bool forceRefresh = false,
  }) async {
    final cacheKey = 'tx_${page}_${pageSize}_${category ?? "all"}_${searchQuery ?? ""}';

    // 1. If online and refresh requested or cache expired, fetch from backend
    if (_connectivity.isOnline && (forceRefresh || page == 1)) {
      try {
        final queryParams = <String, dynamic>{
          'page': page,
          'page_size': pageSize,
          if (category != null && category != 'All') 'category': category,
          if (searchQuery != null && searchQuery.isNotEmpty) 'search': searchQuery,
          if (startDate != null) 'start_date': startDate.toIso8601String(),
          if (endDate != null) 'end_date': endDate.toIso8601String(),
        };

        final response = await _apiClient.get(
          ApiConstants.transactions,
          queryParameters: queryParams,
        );

        final rawList = response is List ? response : (response['items'] as List? ?? []);
        final transactions = rawList
            .whereType<Map<String, dynamic>>()
            .map((json) => Transaction.fromJson(json))
            .toList();

        // Update local read cache
        await _localCache.cacheJson(cacheKey, {
          'items': transactions.map((t) => t.toJson()).toList(),
        });

        return transactions;
      } catch (e) {
        // Fall back to local read cache if network call fails
      }
    }

    // 2. Read from local cache
    final (cachedData, _) = await _localCache.getCachedJson(cacheKey);
    if (cachedData != null && cachedData.containsKey('items')) {
      final cachedList = (cachedData['items'] as List<dynamic>)
          .whereType<Map<String, dynamic>>()
          .map((json) => Transaction.fromJson(json))
          .toList();
      return cachedList;
    }

    return [];
  }

  @override
  Future<Transaction> createTransaction({
    required double amount,
    required String category,
    required String description,
    required DateTime date,
    bool isIncome = false,
    bool isRecurring = false,
  }) async {
    final payload = {
      'amount': amount,
      'category': category,
      'description': description,
      'date': date.toIso8601String(),
      'is_income': isIncome,
      'is_recurring': isRecurring,
    };

    if (_connectivity.isOnline) {
      try {
        final response = await _apiClient.post(
          ApiConstants.transactions,
          data: payload,
        );
        return Transaction.fromJson(response as Map<String, dynamic>);
      } catch (_) {
        // Enqueue offline if network request fails
      }
    }

    // Offline optimistic creation with sync queue
    final optimisticId = 'offline_${DateTime.now().millisecondsSinceEpoch}';
    final optimisticTx = Transaction(
      id: optimisticId,
      amount: amount,
      category: category,
      description: description,
      date: date,
      isIncome: isIncome,
      isRecurring: isRecurring,
      isSynced: false,
    );

    await _localCache.enqueueOfflineMutation(
      action: 'CREATE_TRANSACTION',
      endpoint: ApiConstants.transactions,
      payload: payload,
    );

    return optimisticTx;
  }

  @override
  Future<void> deleteTransaction(String id) async {
    if (_connectivity.isOnline) {
      try {
        await _apiClient.delete('${ApiConstants.transactions}/$id');
        return;
      } catch (_) {
        // Enqueue offline deletion
      }
    }

    await _localCache.enqueueOfflineMutation(
      action: 'DELETE_TRANSACTION',
      endpoint: '${ApiConstants.transactions}/$id',
      payload: {'id': id},
    );
  }

  @override
  Future<void> syncOfflineQueue() async {
    if (!_connectivity.isOnline) return;

    final queue = await _localCache.getPendingSyncQueue();
    for (final item in queue) {
      final queueId = item['queue_id'] as int;
      final action = item['action'] as String;
      final endpoint = item['endpoint'] as String;

      try {
        if (action == 'CREATE_TRANSACTION') {
          await _apiClient.post(endpoint, data: item['payload']);
        } else if (action == 'DELETE_TRANSACTION') {
          await _apiClient.delete(endpoint);
        }
        await _localCache.removeSyncQueueItem(queueId);
      } catch (_) {
        // Retry next sync interval
      }
    }
  }
}
