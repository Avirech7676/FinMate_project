/// Financial overview aggregate received from `/api/v1/analytics/overview`.
class FinancialOverview {
  final double totalIncome;
  final double totalExpenses;
  final double netSavings;
  final double savingsRate;
  final int transactionCount;
  final double healthScore;
  final String cashFlowRisk;
  final Map<String, double> categoryBreakdown;
  final DateTime lastUpdated;

  const FinancialOverview({
    required this.totalIncome,
    required this.totalExpenses,
    required this.netSavings,
    required this.savingsRate,
    required this.transactionCount,
    required this.healthScore,
    required this.cashFlowRisk,
    required this.categoryBreakdown,
    required this.lastUpdated,
  });

  factory FinancialOverview.fromJson(Map<String, dynamic> json) {
    final income = (json['total_income'] as num?)?.toDouble() ?? 0.0;
    final expenses = (json['total_expenses'] as num?)?.toDouble() ?? 0.0;
    final savings = (json['net_savings'] as num?)?.toDouble() ?? (income - expenses);
    final rate = (json['savings_rate'] as num?)?.toDouble() ?? (income > 0 ? savings / income : 0.0);

    final rawBreakdown = json['category_breakdown'] as Map<String, dynamic>? ?? {};
    final breakdown = <String, double>{};
    rawBreakdown.forEach((k, v) {
      if (v is num) breakdown[k] = v.toDouble();
    });

    return FinancialOverview(
      totalIncome: income,
      totalExpenses: expenses,
      netSavings: savings,
      savingsRate: rate,
      transactionCount: (json['transaction_count'] as num?)?.toInt() ?? 0,
      healthScore: (json['health_score'] as num?)?.toDouble() ?? 75.0,
      cashFlowRisk: json['cash_flow_risk'] as String? ?? 'LOW',
      categoryBreakdown: breakdown,
      lastUpdated: json['last_updated'] != null
          ? DateTime.tryParse(json['last_updated'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_income': totalIncome,
      'total_expenses': totalExpenses,
      'net_savings': netSavings,
      'savings_rate': savingsRate,
      'transaction_count': transactionCount,
      'health_score': healthScore,
      'cash_flow_risk': cashFlowRisk,
      'category_breakdown': categoryBreakdown,
      'last_updated': lastUpdated.toIso8601String(),
    };
  }
}
