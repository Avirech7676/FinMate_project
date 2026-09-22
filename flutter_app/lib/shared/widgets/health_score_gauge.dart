import 'dart:math' as math;
import 'package:flutter/material.dart';

/// A 60 FPS hardware-accelerated Radial Gauge rendered via [CustomPainter].
class HealthScoreGauge extends StatefulWidget {
  final double score; // 0 to 100
  final double size;

  const HealthScoreGauge({
    super.key,
    required this.score,
    this.size = 180.0,
  });

  @override
  State<HealthScoreGauge> createState() => _HealthScoreGaugeState();
}

class _HealthScoreGaugeState extends State<HealthScoreGauge>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _animation = Tween<double>(begin: 0.0, end: widget.score).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
    _controller.forward();
  }

  @override
  void didUpdateWidget(HealthScoreGauge oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.score != widget.score) {
      _animation = Tween<double>(begin: _animation.value, end: widget.score).animate(
        CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
      );
      _controller
        ..reset()
        ..forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _GaugePainter(score: _animation.value),
          child: SizedBox(
            width: widget.size,
            height: widget.size,
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _animation.value.toInt().toString(),
                    style: TextStyle(
                      fontSize: widget.size * 0.24,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -1.0,
                      color: _getColorForScore(_animation.value),
                    ),
                  ),
                  Text(
                    'HEALTH SCORE',
                    style: TextStyle(
                      fontSize: widget.size * 0.065,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                      color: const Color(0xFF94A3B8),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Color _getColorForScore(double score) {
    if (score >= 80) return const Color(0xFF10B981); // Emerald
    if (score >= 60) return const Color(0xFF38BDF8); // Sky
    if (score >= 40) return const Color(0xFFF59E0B); // Amber
    return const Color(0xFFEF4444); // Red
  }
}

class _GaugePainter extends CustomPainter {
  final double score;

  _GaugePainter({required this.score});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width / 2) - 14;
    const strokeWidth = 14.0;
    const startAngle = 0.75 * math.pi; // 135 deg
    const sweepAngle = 1.5 * math.pi; // 270 deg

    // Background track
    final bgPaint = Paint()
      ..color = const Color(0xFF1E293B)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      bgPaint,
    );

    // Active progress arc with gradient
    final progressSweep = sweepAngle * (score / 100).clamp(0.0, 1.0);
    final gradient = SweepGradient(
      startAngle: startAngle,
      endAngle: startAngle + sweepAngle,
      colors: const [
        Color(0xFFEF4444), // Coral Red
        Color(0xFFF59E0B), // Amber
        Color(0xFF38BDF8), // Cyan
        Color(0xFF10B981), // Emerald
      ],
    );

    final progressPaint = Paint()
      ..shader = gradient.createShader(Rect.fromCircle(center: center, radius: radius))
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      progressSweep,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _GaugePainter oldDelegate) => oldDelegate.score != score;
}
