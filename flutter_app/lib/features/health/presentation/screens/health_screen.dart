import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/widgets/health_score_gauge.dart';
import '../../dashboard/presentation/dashboard_providers.dart';

class HealthScreen extends ConsumerWidget {
  const HealthScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final healthAsync = ref.watch(healthScoreProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('Financial Health Intelligence'),
      ),
      body: healthAsync.when(
        data: (health) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: HealthScoreGauge(score: health.overallScore, size: 200),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Text(
                  health.explanation,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 14, color: Color(0xFFF1F5F9), height: 1.4),
                ),
              ),
              const SizedBox(height: 24),

              const Text(
                'SCORE PILLARS & WEIGHTS',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                  color: Color(0xFF64748B),
                ),
              ),
              const SizedBox(height: 12),
              ...health.components.map((comp) {
                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF334155), width: 0.8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            comp.name,
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFFF8FAFC),
                            ),
                          ),
                          Text(
                            '${comp.score.toInt()} / 100',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: comp.score >= 70
                                  ? const Color(0xFF10B981)
                                  : const Color(0xFFF59E0B),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: (comp.score / 100).clamp(0.0, 1.0),
                          backgroundColor: const Color(0xFF0F172A),
                          color: comp.score >= 70
                              ? const Color(0xFF10B981)
                              : const Color(0xFFF59E0B),
                          minHeight: 6,
                        ),
                      ),
                      if (comp.explanation.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(
                          comp.explanation,
                          style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                        ),
                      ],
                    ],
                  ),
                );
              }),
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Text('Failed to load health score: $err',
              style: const TextStyle(color: Colors.red)),
        ),
      ),
    );
  }
}
