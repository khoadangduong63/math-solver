import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/history_entry.dart';
import '../providers.dart';

class HistoryPage extends ConsumerWidget {
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(historyProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('History')),
      body: history.when(
        data: (items) => ListView.builder(
          itemCount: items.length,
          itemBuilder: (context, index) {
            final HistoryEntry item = items[index];
            final titleText = item.input.split('\n').first;
            Widget? leading;
            if (item.imagePath != null) {
              final file = File(item.imagePath!);
              leading = file.existsSync()
                  ? Image.file(file, width: 48, height: 48, fit: BoxFit.cover)
                  : const Icon(Icons.image_not_supported);
            }
            return ListTile(
              leading: leading,
              title: Text(
                titleText.isEmpty ? 'Problem ${index + 1}' : titleText,
              ),
              subtitle: Text(item.result.finalAnswer),
              onTap: () => context.push(
                '/solution',
                extra: {
                  'result': item.result,
                  'question': item.imagePath == null ? item.input : null,
                  'imagePath': item.imagePath,
                  'timestamp': item.timestamp,
                },
              ),
            );
          },
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, st) => Center(child: Text('Error: $e')),
      ),
    );
  }
}
