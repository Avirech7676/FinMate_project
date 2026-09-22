import 'package:flutter/material.dart';
import '../../../../core/concurrency/task_contracts.dart';
import '../../../../core/concurrency/compute_runner.dart';

class CsvImportScreen extends StatefulWidget {
  const CsvImportScreen({super.key});

  @override
  State<CsvImportScreen> createState() => _CsvImportScreenState();
}

class _CsvImportScreenState extends State<CsvImportScreen> {
  bool _isProcessing = false;
  double _progress = 0.0;
  String _statusText = 'Ready to ingest CSV';
  Map<String, dynamic>? _parseResult;
  int _lastExecutionTimeMs = 0;

  /// Generates a synthetic dataset of N rows to demonstrate off-thread isolate processing.
  String _generateSampleCsv(int rowCount) {
    final buffer = StringBuffer('Date,Description,Amount,Category\n');
    final categories = ['Food', 'Housing', 'Transportation', 'Utilities', 'Entertainment'];
    for (int i = 1; i <= rowCount; i++) {
      final date = '2026-09-${(i % 28 + 1).toString().padLeft(2, "0")}';
      final desc = 'Merchant Transaction #$i, "Batch A"';
      final amount = (12.50 + (i % 85)).toStringAsFixed(2);
      final cat = categories[i % categories.length];
      buffer.write('$date,"$desc",$amount,$cat\n');
    }
    return buffer.toString();
  }

  Future<void> _runCsvIsolateParse(int rowCount) async {
    setState(() {
      _isProcessing = true;
      _progress = 0.0;
      _statusText = 'Generating synthetic CSV with $rowCount rows...';
      _parseResult = null;
    });

    final csvText = _generateSampleCsv(rowCount);

    final task = WorkerTask(
      taskId: 'csv_${DateTime.now().millisecondsSinceEpoch}',
      type: TaskType.parseCsv,
      payload: csvText,
    );

    // Execute in the dedicated Isolate Worker Pool with streaming progress
    final response = await ComputeRunner.runPooled(
      task,
      onProgress: (progress) {
        setState(() {
          _progress = progress.percentage;
          _statusText = progress.statusMessage ?? 'Parsing records...';
        });
      },
    );

    setState(() {
      _isProcessing = false;
      _progress = 1.0;
      _lastExecutionTimeMs = response.executionTimeMs;
      if (response.isSuccess) {
        _parseResult = response.result as Map<String, dynamic>;
        _statusText = 'Successfully parsed in ${_lastExecutionTimeMs}ms off-thread.';
      } else {
        _statusText = 'Parsing failed: ${response.errorMessage}';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('Background CSV Ingestion'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF1E293B),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.bolt_rounded, color: Color(0xFFF59E0B)),
                      SizedBox(width: 8),
                      Text(
                        'DART WORKER ISOLATE ENGINE',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                          color: Color(0xFFF59E0B),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Large CSV parsing runs entirely in a persistent background Dart isolate with a separate memory heap. The UI thread remains silky smooth at 60 FPS while streaming progress via SendPort.',
                    style: TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Benchmark Trigger Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isProcessing ? null : () => _runCsvIsolateParse(2000),
                    child: const Text('2,000 Rows'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isProcessing ? null : () => _runCsvIsolateParse(10000),
                    child: const Text('10,000 Rows'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Progress Bar & Status
            if (_isProcessing || _progress > 0) ...[
              LinearProgressIndicator(
                value: _progress,
                backgroundColor: const Color(0xFF1E293B),
                color: const Color(0xFF10B981),
                minHeight: 8,
                borderRadius: BorderRadius.circular(4),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _statusText,
                    style: const TextStyle(fontSize: 13, color: Color(0xFFF1F5F9)),
                  ),
                  Text(
                    '${(_progress * 100).toInt()}%',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF10B981),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
            ],

            // Parse Results Preview
            if (_parseResult != null) ...[
              const Text(
                'PARSED BATCH PREVIEW',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                  color: Color(0xFF64748B),
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Column(
                  children: [
                    _InfoRow('Total Records', '${_parseResult!['totalCount']}'),
                    _InfoRow('Valid Transactions', '${_parseResult!['validCount']}'),
                    _InfoRow('Skipped / Malformed', '${_parseResult!['skippedCount']}'),
                    _InfoRow('Isolate Execution Time', '${_lastExecutionTimeMs}ms'),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Color(0xFF94A3B8), fontSize: 14)),
          Text(
            value,
            style: const TextStyle(
              color: Color(0xFFF8FAFC),
              fontWeight: FontWeight.w700,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}
