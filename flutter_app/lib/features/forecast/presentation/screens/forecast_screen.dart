import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/utils/formatters.dart';
import '../../dashboard/presentation/dashboard_providers.dart';

class ForecastScreen extends ConsumerStatefulWidget {
  const ForecastScreen({super.key});

  @override
  ConsumerState<ForecastScreen> createState() => _ForecastScreenState();
}

class _ForecastScreenState extends ConsumerState<ForecastScreen> {
  String _selectedHorizon = '30d';

  @override
  Widget build(BuildContext context) {
    final forecastAsync = ref.watch(forecastFamilyProvider(_selectedHorizon));

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('Holt-Winters Forecasting'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Horizon Selector (7d, 30d, 90d)
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: '7d', label: Text('7 Days')),
                ButtonSegment(value: '30d', label: Text('30 Days')),
                ButtonSegment(value: '90d', label: Text('90 Days')),
              ],
              selected: {_selectedHorizon},
              onSelectionChanged: (set) => setState(() => _selectedHorizon = set.first),
              style: ButtonStyle(
                backgroundColor: MaterialStateProperty.resolveWith<Color>(
                  (states) => states.contains(MaterialState.selected)
                      ? const Color(0xFF6366F1)
                      : const Color(0xFF1E293B),
                ),
              ),
            ),
            const SizedBox(height: 24),

            forecastAsync.when(
              data: (forecast) => Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Projected Total Card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: const Color(0xFF334155)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'PROJECTED EXPENDITURE',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                            color: Color(0xFF94A3B8),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          Formatters.currency(forecast.projectedTotal),
                          style: const TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.6,
                            color: Color(0xFF38BDF8),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          forecast.modelNotice,
                          style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Model Authority Badge
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0EA5E9).withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF0EA5E9).withOpacity(0.2)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.verified_outlined, size: 16, color: Color(0xFF38BDF8)),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Engine: ${forecast.modelName}',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF38BDF8),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Forecast Points List
                  const Text(
                    'PROJECTION TIMELINE',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (forecast.points.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 20),
                      child: Text(
                        'Historical dataset baseline required to generate discrete curve.',
                        style: TextStyle(color: Color(0xFF94A3B8)),
                      ),
                    )
                  else
                    ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: forecast.points.length,
                      itemBuilder: (context, index) {
                        final pt = forecast.points[index];
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1E293B),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: const Color(0xFF334155), width: 0.6),
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                Formatters.date(pt.date),
                                style: const TextStyle(color: Color(0xFFF1F5F9), fontSize: 14),
                              ),
                              Text(
                                Formatters.currency(pt.predictedAmount),
                                style: const TextStyle(
                                  color: Color(0xFF38BDF8),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                ],
              ),
              loading: () => const Center(
                child: Padding(
                  padding: EdgeInsets.all(40),
                  child: CircularProgressIndicator(),
                ),
              ),
              error: (err, _) => Center(
                child: Text('Failed to load forecast: $err',
                    style: const TextStyle(color: Colors.red)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
