/// Immutable domain entity representing a financial transaction.
class Transaction {
  final String id;
  final double amount;
  final String category;
  final String description;
  final DateTime date;
  final bool isIncome;
  final bool isRecurring;
  final String? anomalyFlag;
  final bool isSynced;

  const Transaction({
    required this.id,
    required this.amount,
    required this.category,
    required this.description,
    required this.date,
    this.isIncome = false,
    this.isRecurring = false,
    this.anomalyFlag,
    this.isSynced = true,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id']?.toString() ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      category: json['category'] as String? ?? 'General',
      description: json['description'] as String? ?? '',
      date: json['date'] != null
          ? DateTime.tryParse(json['date'] as String) ?? DateTime.now()
          : DateTime.now(),
      isIncome: json['is_income'] as bool? ?? (json['type'] == 'income'),
      isRecurring: json['is_recurring'] as bool? ?? false,
      anomalyFlag: json['anomaly_flag'] as String?,
      isSynced: json['is_synced'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'amount': amount,
      'category': category,
      'description': description,
      'date': date.toIso8601String(),
      'is_income': isIncome,
      'is_recurring': isRecurring,
      if (anomalyFlag != null) 'anomaly_flag': anomalyFlag,
    };
  }

  Transaction copyWith({
    String? id,
    double? amount,
    String? category,
    String? description,
    DateTime? date,
    bool? isIncome,
    bool? isRecurring,
    String? anomalyFlag,
    bool? isSynced,
  }) {
    return Transaction(
      id: id ?? this.id,
      amount: amount ?? this.amount,
      category: category ?? this.category,
      description: description ?? this.description,
      date: date ?? this.date,
      isIncome: isIncome ?? this.isIncome,
      isRecurring: isRecurring ?? this.isRecurring,
      anomalyFlag: anomalyFlag ?? this.anomalyFlag,
      isSynced: isSynced ?? this.isSynced,
    );
  }
}
