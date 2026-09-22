enum AnomalyLayer { rule, statistical, machineLearning, unknown }

enum AnomalySeverity { low, medium, high, critical }

/// Domain model representing a detected anomaly across the 3 backend intelligence tiers.
class Anomaly {
  final String id;
  final String transactionId;
  final String description;
  final double amount;
  final String category;
  final DateTime date;
  final String reason;
  final AnomalySeverity severity;
  final AnomalyLayer layer;
  final double? score;

  const Anomaly({
    required this.id,
    required this.transactionId,
    required this.description,
    required this.amount,
    required this.category,
    required this.date,
    required this.reason,
    required this.severity,
    required this.layer,
    this.score,
  });

  factory Anomaly.fromJson(Map<String, dynamic> json) {
    // Map severity
    final sevStr = (json['severity'] as String? ?? 'medium').toLowerCase();
    final severity = switch (sevStr) {
      'low' => AnomalySeverity.low,
      'high' => AnomalySeverity.high,
      'critical' => AnomalySeverity.critical,
      _ => AnomalySeverity.medium,
    };

    // Map layer
    final layerStr = (json['layer'] as String? ?? json['detection_layer'] ?? 'statistical').toLowerCase();
    final layer = switch (layerStr) {
      'rule' => AnomalyLayer.rule,
      'statistical' => AnomalyLayer.statistical,
      'machinelearning' || 'ml' || 'isolation_forest' => AnomalyLayer.machineLearning,
      _ => AnomalyLayer.unknown,
    };

    return Anomaly(
      id: json['id']?.toString() ?? '',
      transactionId: json['transaction_id']?.toString() ?? json['id']?.toString() ?? '',
      description: json['description'] as String? ?? json['merchant']?.toString() ?? 'Unspecified Transaction',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      category: json['category'] as String? ?? 'General',
      date: json['date'] != null
          ? DateTime.tryParse(json['date'] as String) ?? DateTime.now()
          : DateTime.now(),
      reason: json['reason'] as String? ?? 'Unusual spending detected',
      severity: severity,
      layer: layer,
      score: (json['score'] as num?)?.toDouble() ?? (json['confidence'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'transaction_id': transactionId,
      'description': description,
      'amount': amount,
      'category': category,
      'date': date.toIso8601String(),
      'reason': reason,
      'severity': severity.name,
      'layer': layer.name,
      if (score != null) 'score': score,
    };
  }
}
