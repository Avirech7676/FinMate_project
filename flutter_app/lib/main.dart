import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/theme/app_theme.dart';
import 'core/routing/app_router.dart';
import 'core/network/connectivity_service.dart';
import 'features/auth/presentation/auth_providers.dart';
import 'features/auth/presentation/screens/login_screen.dart';
import 'features/dashboard/presentation/dashboard_providers.dart';
import 'features/dashboard/presentation/screens/dashboard_screen.dart';
import 'shared/widgets/connectivity_banner.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: FinMateApp()));
}

class FinMateApp extends ConsumerStatefulWidget {
  const FinMateApp({super.key});

  @override
  ConsumerState<FinMateApp> createState() => _FinMateAppState();
}

class _FinMateAppState extends ConsumerState<FinMateApp> with WidgetsBindingObserver {
  late final AppLifecycleListener _lifecycleListener;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    // Section 21: App Lifecycle Observer
    _lifecycleListener = AppLifecycleListener(
      onResume: () {
        // Refresh financial dashboard when returning to foreground
        ref.read(overviewNotifierProvider.notifier).refresh();
      },
    );
  }

  @override
  void dispose() {
    _lifecycleListener.dispose();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authStateProvider);
    final connectivity = ref.watch(connectivityServiceProvider);

    return MaterialApp(
      title: 'FinMate 2.0',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.dark,
      onGenerateRoute: AppRouter.generateRoute,
      builder: (context, child) {
        return StreamBuilder<NetworkStatus>(
          stream: connectivity.statusStream,
          initialData: connectivity.currentStatus,
          builder: (context, snapshot) {
            final status = snapshot.data ?? NetworkStatus.online;
            return Column(
              children: [
                ConnectivityBanner(status: status),
                Expanded(child: child ?? const SizedBox.shrink()),
              ],
            );
          },
        );
      },
      home: authState.when(
        data: (session) {
          if (session == null) {
            return LoginScreen(onLoginSuccess: () {});
          }
          return DashboardScreen(
            onNavigateToTransactions: () =>
                Navigator.pushNamed(context, AppRouter.transactions),
            onNavigateToAI: () =>
                Navigator.pushNamed(context, AppRouter.aiChat),
            onNavigateToForecast: () =>
                Navigator.pushNamed(context, AppRouter.forecast),
            onNavigateToAnomalies: () =>
                Navigator.pushNamed(context, AppRouter.anomalies),
            onNavigateToSimulation: () =>
                Navigator.pushNamed(context, AppRouter.simulation),
            onNavigateToCsv: () =>
                Navigator.pushNamed(context, AppRouter.csvImport),
          );
        },
        loading: () => const Scaffold(
          backgroundColor: Color(0xFF090D16),
          body: Center(
            child: CircularProgressIndicator(color: Color(0xFF6366F1)),
          ),
        ),
        error: (_, __) => LoginScreen(onLoginSuccess: () {}),
      ),
    );
  }
}
