import 'package:cloud_firestore/cloud_firestore.dart';

import 'solution_result.dart';

class HistoryEntry {
  HistoryEntry({
    required this.id,
    required this.input,
    this.imagePath,
    required this.result,
    required this.timestamp,
  });

  final String id;
  final String input;
  final String? imagePath;
  final SolutionResult result;
  final DateTime? timestamp;

  factory HistoryEntry.fromDoc(DocumentSnapshot<Map<String, dynamic>> doc) {
    final data = doc.data() ?? {};
    return HistoryEntry(
      id: doc.id,
      input: data['input']?.toString() ?? '',
      imagePath: data['imagePath']?.toString(),
      result: SolutionResult.fromJson(
        (data['result'] as Map<String, dynamic>? ?? {}),
      ),
      timestamp: (data['timestamp'] as Timestamp?)?.toDate(),
    );
  }
}
