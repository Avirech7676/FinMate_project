import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../shared/models/simulation_result.dart';
import '../../../../shared/widgets/status_badge.dart';
import '../simulation_providers.dart';

class SimulationScreen extends ConsumerStatefulWidget {
  const SimulationScreen({super.key});

  @override
  ConsumerState<SimulationScreen> createState() => _SimulationScreenState();
}

class _SimulationScreenState extends ConsumerState<SimulationScreen> {
  final _amountController = TextEditingController(text: '350.00');
  final _descController = TextEditingController(text: 'New Smartphone Display');
  String _category = 'Entertainment';

  final List<String> _categories = [
    'Food',
    'Housing',
    'Transportation',
    'Utilities',
    'Entertainment',
    'Healthcare',
    'General',
  ];

  @override
  void dispose() {
    _amountController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _handleSimulate() {
    final amount = double.tryParse(_amountController.text) ?? 0.0;
    if (amount <= 0) return;

    ref.read(simulationNotifierProvider.notifier).runSimulation(
          amount: amount,
          category: _category,
          description: _descController.text.trim(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final simAsync = ref.watch(simulationNotifierProvider);
    final isLoading = simAsync.isLoading;
    final result = simAsync.value;

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('What-If Purchase Simulator'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextField(
                    controller: _descController,
                    decoration: const InputDecoration(labelText: 'Purchase Description'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _amountController,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'Simulated Amount (\$)'),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: _category,
                    dropdownColor: const Color(0xFF1E293B),
                    items: _categories
                        .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                        .toList(),
                    onChanged: (v) => setState(() => _category = v!),
                    decoration: const InputDecoration(labelText: 'Expense Category'),
                  ),
                  const SizedBox(height: 18),
                  ElevatedButton(
                    onPressed: isLoading ? null : _handleSimulate,
                    child: isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Evaluate Purchase'),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            if (result != null) ...[
              _VerdictCard(result: result),
            ],
          ],
        ),
      ),
    );
  }
}

class _VerdictCard extends StatelessWidget {
  final SimulationResult result;

  const _VerdictCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final verdictColor = switch (result.verdict) {
      SimulationVerdict.affordable => const Color(0xFF10B981),
      SimulationVerdict.proceedWithCaution => const Color(0xFFF59E0B),
      SimulationVerdict.unrecommended => const Color(0xFFEF4444),
      SimulationVerdict.unknown => const Color(0xFF94A3B8),
    };

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: verdictColor.withOpacity(0.5), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'SIMULATION VERDICT',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: Color(0xFF94A3B8),
                ),
              ),
              StatusBadge(
                label: result.verdict.displayName,
                color: verdictColor,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            result.explanation,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Color(0xFFF8FAFC),
              height: 1.3,
            ),
          ),
          const SizedBox(height: 16),
          const Divider(color: Color(0xFF334155)),
          const SizedBox(height: 12),
          _ImpactRow('Budget Impact', result.budgetImpact),
          _ImpactRow('Cash-Flow Impact', result.cashFlowImpact),
          _ImpactRow('Goal Impact', result.goalImpact),
        ],
      ),
    );
  }
}

class _ImpactRow extends StatelessWidget {
  final String label;
  final String impact;

  const _ImpactRow(this.label, this.impact);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              impact,
              style: const TextStyle(
                color: Color(0xFFF1F5F9),
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
