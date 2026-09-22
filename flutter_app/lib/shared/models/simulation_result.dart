enum SimulationVerdict {
  affordable,
  proceedWithCaution,
  unrecommended,
  unknown;

  static SimulationVerdict fromString(String? value) {
    return switch (value?.toUpperCase()) {
      'AFFORDABLE' => SimulationVerdict.affordable,
      'PROCEED_WITH_CAUTION' || 'CAUTION' => SimulationVerdict.proceedWithCaution,
      'UNRECOMMENDED' || 'RISKY' => SimulationVerdict.unrecommended,
      _ => SimulationVerdict.unknown,
    };
  }

  String get displayName => switch (this) {
        SimulationVerdict.affordable => 'AFFORDABLE',
        SimulationVerdict.proceedWithCaution => 'PROCEED WITH CAUTION',
        SimulationVerdict.unrecommended => 'UNRECOMMENDED',
        SimulationVerdict.unknown => 'EVALUATED',
      };
}

/// Result returned by `/api/v1/intelligence/simulate-purchase`.
class SimulationResult {
  final SimulationVerdict verdict;
  final String budgetImpact;
  final String cashFlowImpact;
  final String goalImpact;
  final double postPurchaseBalance;
  final double postPurchaseSavingsRate;
  final List<String> warnings;
  final String explanation;

  const SimulationResult({
    required this.verdict,
    required this.budgetImpact,
    required this.cashFlowImpact,
    required this.goalImpact,
    required this.postPurchaseBalance,
    required this.postPurchaseSavingsRate,
    required this.warnings,
    required this.explanation,
  });

  factory SimulationResult.fromJson(Map<String, dynamic> json) {
    final verdict = SimulationVerdict.fromString(json['verdict'] as String?);
    final rawWarnings = json['warnings'] as List<dynamic>? ?? [];

    return SimulationResult(
      verdict: verdict,
      budgetImpact: json['budget_impact'] as String? ?? 'Within monthly budget limit.',
      cashFlowImpact: json['cash_flow_impact'] as String? ?? 'Positive runway maintained.',
      goalImpact: json['goal_impact'] as String? ?? 'No goals compromised.',
      postPurchaseBalance: (json['post_purchase_balance'] as num?)?.toDouble() ?? 0.0,
      postPurchaseSavingsRate: (json['post_purchase_savings_rate'] as num?)?.toDouble() ?? 0.0,
      warnings: rawWarnings.map((w) => w.toString()).toList(),
      explanation: json['explanation'] as String? ?? 'Purchase aligns with current financial pacing.',
    );
  }
}
