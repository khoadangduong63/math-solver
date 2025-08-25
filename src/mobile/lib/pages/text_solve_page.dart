import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:go_router/go_router.dart';

import '../models/solution_result.dart';
import '../providers.dart';

class TextSolvePage extends ConsumerStatefulWidget {
  const TextSolvePage({super.key});

  @override
  ConsumerState<TextSolvePage> createState() => _TextSolvePageState();
}

class _TextSolvePageState extends ConsumerState<TextSolvePage> {
  final _controller = TextEditingController();
  bool _loading = false;

  Future<void> _solve() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    setState(() => _loading = true);
    try {
      final dio = ref.read(dioProvider);
      final res = await dio.post(
        '/solve-text',
        data: {'question': text},
        options: Options(contentType: Headers.jsonContentType),
      );
      final result = SolutionResult.fromJson(res.data as Map<String, dynamic>);
      final timestamp = DateTime.now();
      await saveToHistory(ref, text, result, timestamp: timestamp);
      if (mounted) {
        context.push(
          '/solution',
          extra: {
            'result': result,
            'question': text,
            'timestamp': timestamp,
          },
        );
      }
    } catch (e) {
      if (mounted) {
        String message = 'Error: $e';
        if (e is DioException) {
          message = 'Error calling ${e.requestOptions.uri}: ${e.message}';
        }
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(message)));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Text Solve')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _controller,
              decoration: const InputDecoration(labelText: 'Enter problem'),
              onSubmitted: (_) => _solve(),
            ),
          ),
          ElevatedButton(
            onPressed: _loading ? null : _solve,
            child: _loading
                ? const CircularProgressIndicator()
                : const Text('Solve'),
          ),
        ],
      ),
    );
  }
}
