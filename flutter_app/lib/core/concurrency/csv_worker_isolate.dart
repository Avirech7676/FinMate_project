import 'dart:isolate';
import 'task_contracts.dart';

/// Worker isolate implementation for high-throughput, non-blocking CSV parsing.
/// Correctly handles RFC 4180 quotes, escaped commas, and emits incremental progress.
class CsvWorkerIsolate {
  CsvWorkerIsolate._();

  static Map<String, dynamic> process(WorkerTask task, SendPort progressPort) {
    final csvContent = task.payload as String;
    final lines = csvContent.split(RegExp(r'\r\n|\r|\n'));
    final totalLines = lines.length;

    if (totalLines <= 1) {
      return {
        'headers': <String>[],
        'rows': <Map<String, dynamic>>[],
        'totalCount': 0,
        'validCount': 0,
        'skippedCount': 0,
      };
    }

    // Parse header row
    final headers = _parseCsvLine(lines.first);
    final rows = <Map<String, dynamic>>[];
    int skippedCount = 0;

    final progressInterval = (totalLines / 20).ceil().clamp(1, 1000);

    for (int i = 1; i < totalLines; i++) {
      final line = lines[i].trim();
      if (line.isEmpty) {
        skippedCount++;
        continue;
      }

      final values = _parseCsvLine(line);
      if (values.length != headers.length) {
        skippedCount++;
        continue;
      }

      final rowMap = <String, dynamic>{};
      for (int h = 0; h < headers.length; h++) {
        rowMap[headers[h].trim().toLowerCase()] = values[h].trim();
      }
      rows.add(rowMap);

      // Emit incremental streaming progress back to UI isolate
      if (i % progressInterval == 0 || i == totalLines - 1) {
        final percentage = i / totalLines;
        progressPort.send(
          WorkerProgress(
            taskId: task.taskId,
            percentage: percentage,
            processedCount: i,
            totalCount: totalLines,
            statusMessage: 'Parsed $i of $totalLines records (${(percentage * 100).toInt()}%)',
          ),
        );
      }
    }

    return {
      'headers': headers,
      'rows': rows,
      'totalCount': totalLines - 1,
      'validCount': rows.length,
      'skippedCount': skippedCount,
    };
  }

  /// Parses a single line compliant with RFC 4180.
  static List<String> _parseCsvLine(String line) {
    final result = <String>[];
    final buffer = StringBuffer();
    bool insideQuotes = false;

    for (int i = 0; i < line.length; i++) {
      final char = line[i];

      if (char == '"') {
        if (insideQuotes && i + 1 < line.length && line[i + 1] == '"') {
          buffer.write('"');
          i++; // Skip escaped quote
        } else {
          insideQuotes = !insideQuotes;
        }
      } else if (char == ',' && !insideQuotes) {
        result.add(buffer.toString());
        buffer.clear();
      } else {
        buffer.write(char);
      }
    }

    result.add(buffer.toString());
    return result;
  }
}
