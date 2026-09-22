import 'package:flutter/material.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';
import '../../features/transactions/presentation/screens/transactions_screen.dart';
import '../../features/forecast/presentation/screens/forecast_screen.dart';
import '../../features/anomalies/presentation/screens/anomalies_screen.dart';
import '../../features/simulation/presentation/screens/simulation_screen.dart';
import '../../features/csv_import/presentation/screens/csv_import_screen.dart';
import '../../features/ai/presentation/screens/ai_chat_screen.dart';
import '../../features/health/presentation/screens/health_screen.dart';

/// Centralized route definitions and navigation dispatching.
class AppRouter {
  AppRouter._();

  static const String dashboard = '/';
  static const String transactions = '/transactions';
  static const String forecast = '/forecast';
  static const String anomalies = '/anomalies';
  static const String simulation = '/simulation';
  static const String csvImport = '/csv-import';
  static const String aiChat = '/ai-chat';
  static const String health = '/health';

  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case dashboard:
        return MaterialPageRoute(
          builder: (ctx) => DashboardScreen(
            onNavigateToTransactions: () => Navigator.pushNamed(ctx, transactions),
            onNavigateToAI: () => Navigator.pushNamed(ctx, aiChat),
            onNavigateToForecast: () => Navigator.pushNamed(ctx, forecast),
            onNavigateToAnomalies: () => Navigator.pushNamed(ctx, anomalies),
            onNavigateToSimulation: () => Navigator.pushNamed(ctx, simulation),
            onNavigateToCsv: () => Navigator.pushNamed(ctx, csvImport),
          ),
        );

      case transactions:
        return MaterialPageRoute(builder: (_) => const TransactionsScreen());

      case forecast:
        return MaterialPageRoute(builder: (_) => const ForecastScreen());

      case anomalies:
        return MaterialPageRoute(builder: (_) => const AnomaliesScreen());

      case simulation:
        return MaterialPageRoute(builder: (_) => const SimulationScreen());

      case csvImport:
        return MaterialPageRoute(builder: (_) => const CsvImportScreen());

      case aiChat:
        return MaterialPageRoute(builder: (_) => const AIChatScreen());

      case health:
        return MaterialPageRoute(builder: (_) => const HealthScreen());

      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(child: Text('Route not found: ${settings.name}')),
          ),
        );
    }
  }
}
