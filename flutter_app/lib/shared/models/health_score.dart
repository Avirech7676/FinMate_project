/// Component breakdown of the explainable financial health score.
class HealthScoreComponent {
  final String name;
  final double score; // 0 - 100
  final double weight;
  final String status;
  final String explanation;

  const HealthScoreComponent({
    required this.name,
    required this.score,
    required this.weight,
    required this.status,
    required this.explanation,
  });

  factory HealthScoreComponent.fromJson(Map<String, dynamic> json) {
    return HealthScoreComponent(
      name: json['name'] as String? ?? 'Component',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      weight: (json['weight'] as num?)?.toDouble() ?? 0.2,
      status: json['status'] as String? ?? 'GOOD',
      explanation: json['explanation'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'score': score,
        'weight': weight,
        'status': status,
        'explanation': explanation,
      };
}

/// Explainable financial health score supplied authoritatively by FastAPI backend.
class HealthScore {
  final double overallScore;
  final String tier; // EXCELLENT, GOOD, FAIR, POOR, CRITICAL
  final String explanation;
  final List<HealthScoreComponent> components;
  final List<String> actionableRecommendations;
  final DateTime calculatedAt;

  const HealthScore({
    required this.overallScore,
    required this.tier,
    required this.explanation,
    required this.components,
    required this.actionableRecommendations,
    required this.calculatedAt,
  });

  factory HealthScore.fromJson(Map<String, dynamic> json) {
    final rawComps = json['components'] as List<dynamic>? ?? [];
    final components = rawComps
        .whereType<Map<String, dynamic>>()
        .map((c) => HealthScoreComponent.fromJson(c))
        .toList();

    final recs = (json['recommendations'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();

    return HealthScore(
      overallScore: (json['overall_score'] as num?)?.toDouble() ??
          (json['score'] as num?)?.toDouble() ??
          75.0,
      tier: json['tier'] as String? ?? 'GOOD',
      explanation: json['explanation'] as String? ??
          'Your financial health reflects consistent savings and controlled recurring commitments.',
      components: components,
      actionableRecommendations: recs,
      calculatedAt: json['calculated_at'] != null
          ? DateTime.tryParse(json['calculated_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}
