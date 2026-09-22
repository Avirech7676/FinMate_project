import 'package:flutter/material.dart';
import '../../core/network/connectivity_service.dart';

/// Subtle status indicator banner reflecting real-time network connectivity.
class ConnectivityBanner extends StatelessWidget {
  final NetworkStatus status;

  const ConnectivityBanner({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    if (status == NetworkStatus.online) {
      return const SizedBox.shrink();
    }

    final isOffline = status == NetworkStatus.offline;
    final bgColor = isOffline ? const Color(0xFFEF4444) : const Color(0xFFF59E0B);
    final text = isOffline
        ? 'Offline Mode — Local SQLite cache active. Changes will sync automatically.'
        : 'Reconnecting to FinMate servers...';
    final icon = isOffline ? Icons.cloud_off_rounded : Icons.sync_rounded;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: bgColor.withOpacity(0.92),
      child: SafeArea(
        bottom: false,
        child: Row(
          children: [
            Icon(icon, size: 16, color: Colors.white),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                text,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
