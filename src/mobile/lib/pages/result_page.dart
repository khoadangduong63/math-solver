import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_math_fork/flutter_math.dart';
import 'package:share_plus/share_plus.dart';

import '../models/solution_result.dart';

class ResultPage extends StatelessWidget {
  const ResultPage({
    super.key,
    required this.result,
    this.question,
    this.imagePath,
    this.timestamp,
  });

  final SolutionResult result;
  final String? question;
  final String? imagePath;
  final DateTime? timestamp;

  String? _formatTimestamp(DateTime? ts) {
    if (ts == null) return null;
    final dt = ts.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${dt.year}-${two(dt.month)}-${two(dt.day)} ${two(dt.hour)}:${two(dt.minute)}';
  }

  void _copy(BuildContext context) {
    Clipboard.setData(ClipboardData(text: result.finalAnswer));
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Copied to clipboard')));
  }

  void _share() {
    Share.share(result.finalAnswer);
  }

  @override
  Widget build(BuildContext context) {
    final ts = _formatTimestamp(timestamp);
    return Scaffold(
      appBar: AppBar(),
      bottomNavigationBar: BottomAppBar(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            IconButton(
              icon: const Icon(Icons.copy),
              onPressed: () => _copy(context),
              tooltip: 'Copy',
            ),
            IconButton(
              icon: const Icon(Icons.share),
              onPressed: _share,
              tooltip: 'Share',
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                if (imagePath != null)
                  _buildImage(imagePath!)
                else if (question != null)
                  Expanded(
                    child: Text(
                      question!.split('\n').first,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                const Spacer(),
                if (ts != null)
                  Text(
                    ts,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            ),
            const SizedBox(height: 16),
            Text('Final Answer: ${result.finalAnswer}',
                style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            if (result.steps.isNotEmpty) ...[
              Text('Steps', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...result.steps.map(
                (s) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (s.title.isNotEmpty)
                        Text(s.title,
                            style: const TextStyle(fontWeight: FontWeight.bold)),
                      if (s.explanation.isNotEmpty) Text(s.explanation),
                      if (s.latex != null && s.latex!.isNotEmpty)
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Math.tex(s.latex!,
                              textStyle: const TextStyle(fontSize: 16)),
                        ),
                    ],
                  ),
                ),
              ),
            ],
            if (result.ocrText != null && result.ocrText!.isNotEmpty)
              ExpansionTile(
                title: const Text('OCR Text from Image'),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: SelectableText(result.ocrText!),
                  ),
                ],
              ),
            if (result.latex.isNotEmpty)
              ExpansionTile(
                title: const Text('Show derivation (LaTeX)'),
                children: [
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.all(16),
                    child: Math.tex(result.latex,
                        textStyle: const TextStyle(fontSize: 16)),
                  ),
                ],
              ),
            ExpansionTile(
              title: const Text('Raw JSON (debug)'),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: SelectableText(result.toRawJson()),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildImage(String path) {
    final file = File(path);
    if (file.existsSync()) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: Image.file(
          file,
          width: 64,
          height: 64,
          fit: BoxFit.cover,
        ),
      );
    }
    return const Icon(Icons.image_not_supported, size: 64);
  }
}

