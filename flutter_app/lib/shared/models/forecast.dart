class ForecastPoint {
  final DateTime date;
  final double predictedAmount;
  final double? lowerBound;
  final double? upperBound;

  const ForecastPoint({
    required this.date,
    required this.predictedAmount,
    this.lowerBound,
    this.upperBound,
  });

  factory ForecastPoint.fromJson(Map<String, dynamic> json) {
    return ForecastPoint(
      date: DateTime.tryParse(json['date']?.toString() ?? '') ?? DateTime.now(),
      predictedAmount: (json['amount'] as num?)?.toDouble() ??
          (json['predicted'] as num?)?.toDouble() ??
          0.0,
      lowerBound: (json['lower_bound'] as num?)?.toDouble(),
      upperBound: (json['upper_bound'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'date': date.toIso8601String(),
        'predicted': predictedAmount,
        'lower_bound': lowerBound,
        'upper_bound': upperBound,
      };
}

/// Holt-Winters authoritative forecasting response from backend.
class Forecast {
  final String horizon; // 7d, 30d, 90d
  final double projectedTotal;
  final List<ForecastPoint> points;
  final String modelName;
  final String modelNotice;
  final Map<String, dynamic>? metrics;

  const Forecast({
    required this.horizon,
    required this.projectedTotal,
    required this.points,
    required this.modelName,
    required this.modelNotice,
    this.metrics,
  });

  factory Forecast.fromJson(Map<String, dynamic> json) {
    final rawPoints = (json['forecast'] as List<dynamic>? ??
        json['points'] as List<dynamic>? ??
        []);

    final points = rawPoints
        .whereType<Map<String, dynamic>>()
        .map((p) => ForecastPoint.fromJson(p))
        .toList();

    return Forecast(
      horizon: json['horizon'] as String? ?? '30d',
      projectedTotal: (json['projected_total'] as num?)?.toDouble() ??
          (json['total_projected'] as num?)?.toDouble() ??
          0.0,
      points: points,
      modelName: json['model_name'] as String? ?? 'Holt-Winters Triple Exponential Smoothing',
      modelNotice: json['model_notice'] as String? ??
          'Forecast computed authoritatively by backend time-series engine.',
      metrics: json['metrics'] as Map<String, dynamic>?,
    );
  }
}
