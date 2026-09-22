import 'dart:async';
import 'package:connectivity_plus/connectivity_plus.dart';

enum NetworkStatus { online, offline, reconnecting }

/// Manages and broadcasts network connectivity transitions via a Stream.
class ConnectivityService {
  final Connectivity _connectivity;
  final StreamController<NetworkStatus> _controller = StreamController<NetworkStatus>.broadcast();

  NetworkStatus _lastStatus = NetworkStatus.online;

  ConnectivityService({Connectivity? connectivity})
      : _connectivity = connectivity ?? Connectivity() {
    _init();
  }

  Stream<NetworkStatus> get statusStream => _controller.stream;
  NetworkStatus get currentStatus => _lastStatus;
  bool get isOnline => _lastStatus == NetworkStatus.online;

  void _init() {
    _connectivity.onConnectivityChanged.listen((results) {
      final isConnected = results.any((r) => r != ConnectivityResult.none);
      final newStatus = isConnected ? NetworkStatus.online : NetworkStatus.offline;

      if (_lastStatus == NetworkStatus.offline && newStatus == NetworkStatus.online) {
        _lastStatus = NetworkStatus.reconnecting;
        _controller.add(NetworkStatus.reconnecting);
        Future.delayed(const Duration(milliseconds: 1500), () {
          _lastStatus = NetworkStatus.online;
          _controller.add(NetworkStatus.online);
        });
      } else {
        _lastStatus = newStatus;
        _controller.add(newStatus);
      }
    });
  }

  Future<bool> checkConnection() async {
    final results = await _connectivity.checkConnectivity();
    final isConnected = results.any((r) => r != ConnectivityResult.none);
    _lastStatus = isConnected ? NetworkStatus.online : NetworkStatus.offline;
    return isConnected;
  }

  void dispose() {
    _controller.close();
  }
}
