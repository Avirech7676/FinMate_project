import 'dart:isolate';
import 'task_contracts.dart';

/// Worker isolate implementation for local report generation and weekly briefing rollups.
class ReportWorkerIsolate {
  ReportWorkerIsolate._();

  static Map<String, dynamic> process(WorkerTask task, SendPort progressPort) {
    final payload = task.payload as Map<String, dynamic>;
    final transactions = (payload['transactions'] as List<dynamic>)
        .cast<Map<String, dynamic>>();

    final categoryTotals = <String, double>{};
    double totalIncome = 0.0;
    double totalExpense = 0.0;

    final total = transactions.length;
    final interval = (total / 10).ceil().clamp(1, 100);

    for (int i = 0; i < total; i++) {
      final tx = transactions[i];
      final amount = (tx['amount'] as num).toDouble();
      final isIncome = tx['is_income'] == true;
      final category = (tx['category'] as String?) ?? 'Uncategorized';

      if (isIncome) {
        totalIncome += amount;
      } else {
        totalExpense += amount;
        categoryTotals[category] = (categoryTotals[category] ?? 0.0) + amount;
      }

      if (i % interval == 0) {
        progressPort.send(
          WorkerProgress(
            taskId: task.taskId,
            percentage: i / total,
            processedCount: i,
            totalCount: total,
            statusMessage: 'Aggregating categories... ($i/$total)',
          ),
        );
      }
    }

    // Sort categories descending
    final sortedCategories = categoryTotals.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    final topSpendingCategories = sortedCategories
        .take(5)
        .map((e) => {
              'category': e.key,
              'amount': e.value,
              'percentage': totalExpense > 0 ? (e.value / totalExpense) : 0.0,
            })
        .toList();

    return {
      'totalIncome': totalIncome,
      'totalExpense': totalExpense,
      'netSavings': totalIncome - totalExpense,
      'savingsRate': totalIncome > 0 ? ((totalIncome - totalExpense) / totalIncome) : 0.0,
      'topCategories': topSpendingCategories,
      'transactionCount': total,
      'generatedAt': DateTime.now().toIso8601String(),
    };
  }
}
