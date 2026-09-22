import 'package:test/test.dart';
import '../lib/core/utils/formatters.dart';
import '../lib/core/utils/validators.dart';

void main() {
  group('Formatters & Validators Unit Tests', () {
    test('Formatters format currency correctly', () {
      expect(Formatters.currency(1234.56), equals('\$1,234.56'));
      expect(Formatters.currency(0.0), equals('\$0.00'));
    });

    test('Formatters format percentages correctly', () {
      expect(Formatters.percentage(0.254), equals('25.4%'));
      expect(Formatters.percentage(1.0), equals('100.0%'));
    });

    test('Validators validate email addresses accurately', () {
      expect(Validators.email('test@finmate.io'), isNull);
      expect(Validators.email('invalid-email'), isNotNull);
      expect(Validators.email(''), isNotNull);
      expect(Validators.email(null), isNotNull);
    });

    test('Validators validate password length', () {
      expect(Validators.password('12345678'), isNull);
      expect(Validators.password('short'), isNotNull);
      expect(Validators.password(''), isNotNull);
    });

    test('Validators validate positive amount', () {
      expect(Validators.positiveAmount('100.50'), isNull);
      expect(Validators.positiveAmount('0'), isNotNull);
      expect(Validators.positiveAmount('-25'), isNotNull);
      expect(Validators.positiveAmount('abc'), isNotNull);
    });
  });
}
