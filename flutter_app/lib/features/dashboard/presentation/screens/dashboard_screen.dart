import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/utils/formatters.dart';
import '../../../../shared/widgets/health_score_gauge.dart';
import '../../../../shared/widgets/metric_card.dart';
import '../../../../shared/widgets/status_badge.dart';
import '../dashboard_providers.dart';
import '../../auth/presentation/auth_providers.dart';

class DashboardScreen extends ConsumerWidget {
  final VoidCallback onNavigateToTransactions;
  final VoidCallback onNavigateToAI;
  final VoidCallback onNavigateToForecast;
  final VoidCallback onNavigateToAnomalies;
  final VoidCallback onNavigateToSimulation;
  final VoidCallback onNavigateToCsv;

  const DashboardScreen({
    super.key,
    required this.onNavigateToTransactions,
    required this.onNavigateToAI,
    required this.onNavigateToForecast,
    required this.onNavigateToAnomalies,
    required this.onNavigateToSimulation,
    required this.onNavigateToCsv,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overviewAsync = ref.watch(overviewNotifierProvider);
    final healthAsync = ref.watch(healthScoreProvider);
    final anomaliesAsync = ref.watch(anomaliesProvider);
    final goalsAsync = ref.watch(goalsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('FinMate 2.0'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh Financial Overview',
            onPressed: () => ref.read(overviewNotifierProvider.notifier).refresh(),
          ),
          IconButton(
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Sign Out',
            onPressed: () => ref.read(authStateProvider.notifier).logout(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await ref.read(overviewNotifierProvider.notifier).refresh();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Health Score Section with Gauge
              Center(
                child: healthAsync.when(
                  data: (health) => Column(
                    children: [
                      HealthScoreGauge(score: health.overallScore),
                      const SizedBox(height: 8),
                      Text(
                        health.explanation,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 13,
                          color: Color(0xFF94A3B8),
                        ),
                      ),
                    ],
                  ),
                  loading: () => const HealthScoreGauge(score: 75.0),
                  error: (_, __) => const HealthScoreGauge(score: 50.0),
                ),
              ),
              const SizedBox(height: 24),

              // KPI Metric Cards Grid
              overviewAsync.when(
                data: (overview) => GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.25,
                  children: [
                    MetricCard(
                      label: 'Monthly Income',
                      value: Formatters.currency(overview.totalIncome),
                      icon: Icons.arrow_downward_rounded,
                      accentColor: const Color(0xFF10B981),
                    ),
                    MetricCard(
                      label: '30-Day Spending',
                      value: Formatters.currency(overview.totalExpenses),
                      icon: Icons.arrow_upward_rounded,
                      accentColor: const Color(0xFFEF4444),
                    ),
                    MetricCard(
                      label: 'Net Savings',
                      value: Formatters.currency(overview.netSavings),
                      icon: Icons.savings_outlined,
                      accentColor: const Color(0xFF6366F1),
                      subtitle: 'Rate: ${Formatters.percentage(overview.savingsRate)}',
                    ),
                    MetricCard(
                      label: 'Cash Flow Risk',
                      value: overview.cashFlowRisk,
                      icon: Icons.shield_outlined,
                      accentColor: overview.cashFlowRisk == 'LOW'
                          ? const Color(0xFF10B981)
                          : const Color(0xFFF59E0B),
                    ),
                  ],
                ),
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (err, _) => Text('Failed to load metrics: $err'),
              ),
              const SizedBox(height: 24),

              // Intelligence Quick Actions
              const Text(
                'INTELLIGENCE & TOOLS',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                  color: Color(0xFF64748B),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.psychology_rounded,
                      label: 'AI Advisor',
                      color: const Color(0xFF6366F1),
                      onTap: onNavigateToAI,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.timeline_rounded,
                      label: 'Forecast',
                      color: const Color(0xFF0EA5E9),
                      onTap: onNavigateToForecast,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.warning_amber_rounded,
                      label: 'Anomalies',
                      color: const Color(0xFFF59E0B),
                      onTap: onNavigateToAnomalies,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.calculate_outlined,
                      label: 'Simulator',
                      color: const Color(0xFF10B981),
                      onTap: onNavigateToSimulation,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.upload_file_rounded,
                      label: 'CSV Isolate',
                      color: const Color(0xFFEC4899),
                      onTap: onNavigateToCsv,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _QuickActionButton(
                      icon: Icons.receipt_long_rounded,
                      label: 'Ledger',
                      color: const Color(0xFF8B5CF6),
                      onTap: onNavigateToTransactions,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 28),

              // Active Anomaly Alert Banner
              anomaliesAsync.when(
                data: (anomalies) {
                  if (anomalies.isEmpty) return const SizedBox.shrink();
                  final top = anomalies.first;
                  return Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFFF59E0B).withOpacity(0.4)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, size: 18, color: Color(0xFFF59E0B)),
                                SizedBox(width: 8),
                                Text(
                                  'ANOMALY DETECTED',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800,
                                    color: Color(0xFFF59E0B),
                                  ),
                                ),
                              ],
                            ),
                            StatusBadge(
                              label: top.layer.name,
                              color: const Color(0xFFF59E0B),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${top.description} — ${Formatters.currency(top.amount)}',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFFF8FAFC),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          top.reason,
                          style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
                        ),
                      ],
                    ),
                  );
                },
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF334155)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(height: 6),
            Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Color(0xFFF1F5F9),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
