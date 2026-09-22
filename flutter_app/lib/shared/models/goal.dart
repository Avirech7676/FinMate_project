/// Domain model for budget and savings goals.
class Goal {
  final String id;
  final String title;
  final double targetAmount;
  final double currentAmount;
  final DateTime targetDate;
  final String category;
  final bool isCompleted;

  const Goal({
    required this.id,
    required this.title,
    required this.targetAmount,
    required this.currentAmount,
    required this.targetDate,
    required this.category,
    this.isCompleted = false,
  });

  double get progressRatio => targetAmount > 0 ? (currentAmount / targetAmount).clamp(0.0, 1.0) : 0.0;
  double get remainingAmount => (targetAmount - currentAmount).clamp(0.0, double.infinity);

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? json['name'] as String? ?? 'Untitled Goal',
      targetAmount: (json['target_amount'] as num?)?.toDouble() ?? 0.0,
      currentAmount: (json['current_amount'] as num?)?.toDouble() ?? 0.0,
      targetDate: json['target_date'] != null
          ? DateTime.tryParse(json['target_date'] as String) ?? DateTime.now()
          : DateTime.now(),
      category: json['category'] as String? ?? 'Savings',
      isCompleted: json['is_completed'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'target_amount': targetAmount,
        'current_amount': currentAmount,
        'target_date': targetDate.toIso8601String(),
        'category': category,
        'is_completed': isCompleted,
      };
}
