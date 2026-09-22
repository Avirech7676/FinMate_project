/// Cash flow projection and insolvency risk analysis from backend.
class CashFlowDay {
  final DateTime date;
  final double projectedBalance;
  final double inflow;
  final double outflow;

  const CashFlowDay({
    required this.date,
    required this.projectedBalance,
    required this.inflow,
    required this.outflow,
  });

  factory CashFlowDay.fromJson(Map<String, dynamic> json) {
    return CashFlowDay(
      date: DateTime.tryParse(json['date']?.toString() ?? '') ?? DateTime.now(),
      projectedBalance: (json['projected_balance'] as num?)?.toDouble() ?? 0.0,
      inflow: (json['inflow'] as num?)?.toDouble() ?? 0.0,
      outflow: (json['outflow'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class CashFlowProjection {
  final double startingBalance;
  final double endingBalance;
  final double minimumProjectedBalance;
  final String riskLevel; // LOW, MODERATE, HIGH, CRITICAL
  final String riskSummary;
  final List<CashFlowDay> dailyProjections;

  const CashFlowProjection({
    required this.startingBalance,
    required this.endingBalance,
    required this.minimumProjectedBalance,
    required this.riskLevel,
    required this.riskSummary,
    required this.dailyProjections,
  });

  factory CashFlowProjection.fromJson(Map<String, dynamic> json) {
    final rawDays = json['projections'] as List<dynamic>? ?? [];
    final days = rawDays
        .whereType<Map<String, dynamic>>()
        .map((d) => CashFlowDay.fromJson(d))
        .toList();

    return CashFlowProjection(
      startingBalance: (json['starting_balance'] as num?)?.toDouble() ?? 0.0,
      endingBalance: (json['ending_balance'] as num?)?.toDouble() ?? 0.0,
      minimumProjectedBalance: (json['minimum_balance'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] as String? ?? 'LOW',
      riskSummary: json['summary'] as String? ?? 'Cash flow remains positive across the projection window.',
      dailyProjections: days,
    );
  }
}
