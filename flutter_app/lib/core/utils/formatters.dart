/// Presentation formatting utilities for currency, percentages, and dates
/// using zero external dependencies for maximum resilience and cross-platform compatibility.
class Formatters {
  Formatters._();

  static const List<String> _months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ];

  /// Formats amount into currency representation (e.g., $1,234.56).
  static String currency(double amount) {
    final isNegative = amount < 0;
    final absAmount = amount.abs();
    final parts = absAmount.toStringAsFixed(2).split('.');
    final integerPart = parts[0];
    final decimalPart = parts[1];

    final buffer = StringBuffer();
    int count = 0;
    for (int i = integerPart.length - 1; i >= 0; i--) {
      buffer.write(integerPart[i]);
      count++;
      if (count % 3 == 0 && i > 0) {
        buffer.write(',');
      }
    }
    final formattedInt = buffer.toString().split('').reversed.join('');
    final prefix = isNegative ? '-\$' : '\$';
    return '$prefix$formattedInt.$decimalPart';
  }

  /// Compact currency format (e.g. $1.2M, $45.2K).
  static String compactCurrency(double amount) {
    if (amount >= 1000000) {
      return '\$${(amount / 1000000).toStringAsFixed(1)}M';
    } else if (amount >= 1000) {
      return '\$${(amount / 1000).toStringAsFixed(1)}K';
    }
    return currency(amount);
  }

  /// Formats date to 'MMM d, yyyy' (e.g., 'Sep 22, 2026').
  static String date(DateTime dateTime) {
    final month = _months[dateTime.month - 1];
    return '$month ${dateTime.day}, ${dateTime.year}';
  }

  /// Formats date to ISO-8601 'yyyy-MM-dd'.
  static String isoDate(DateTime dateTime) {
    final y = dateTime.year.toString().padLeft(4, '0');
    final m = dateTime.month.toString().padLeft(2, '0');
    final d = dateTime.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  /// Formats ratio to percentage string (e.g. 0.25 -> 25.0%).
  static String percentage(double ratio) {
    return '${(ratio * 100).toStringAsFixed(1)}%';
  }
}
