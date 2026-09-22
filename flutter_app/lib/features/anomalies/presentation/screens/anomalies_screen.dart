import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/utils/formatters.dart';
import '../../../../shared/models/anomaly.dart';
import '../../../../shared/widgets/status_badge.dart';
import '../../dashboard/presentation/dashboard_providers.dart';

class AnomaliesScreen extends ConsumerWidget {
  const AnomaliesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final anomaliesAsync = ref.watch(anomaliesProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('3-Tier Anomaly Intelligence'),
      ),
      body: anomaliesAsync.when(
        data: (anomalies) {
          if (anomalies.isEmpty) {
            return const Center(
              child: Text(
                'No financial anomalies detected across Rule, Statistical, or ML tiers.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Color(0xFF94A3B8)),
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: anomalies.length,
            itemBuilder: (context, index) {
              final a = anomalies[index];
              final sevColor = _getSeverityColor(a.severity);

              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: sevColor.withOpacity(0.4), width: 1),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        StatusBadge(
                          label: a.layer.name.toUpperCase(),
                          color: const Color(0xFF6366F1),
                          icon: Icons.layers_outlined,
                        ),
                        StatusBadge(
                          label: a.severity.name.toUpperCase(),
                          color: sevColor,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      a.description,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFFF8FAFC),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${Formatters.currency(a.amount)} • ${a.category} • ${Formatters.date(a.date)}',
                      style: const TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline_rounded, size: 14, color: sevColor),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              a.reason,
                              style: TextStyle(fontSize: 12, color: sevColor),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text('Failed to load anomalies: $err',
              style: const TextStyle(color: Colors.red)),
        ),
      ),
    );
  }

  Color _getSeverityColor(AnomalySeverity sev) {
    return switch (sev) {
      AnomalySeverity.critical => const Color(0xFFEF4444),
      AnomalySeverity.high => const Color(0xFFF97316),
      AnomalySeverity.medium => const Color(0xFFF59E0B),
      AnomalySeverity.low => const Color(0xFF10B981),
    };
  }
}
