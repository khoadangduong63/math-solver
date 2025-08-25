import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/foundation.dart';

import 'models/history_entry.dart';
import 'models/solution_result.dart';
import 'config.dart';

final firebaseAuthProvider = Provider<FirebaseAuth>((ref) {
  return FirebaseAuth.instance;
});

final firestoreProvider = Provider<FirebaseFirestore>((ref) {
  return FirebaseFirestore.instance;
});

final authProvider = FutureProvider<User?>((ref) async {
  final auth = ref.watch(firebaseAuthProvider);
  var user = auth.currentUser;
  if (user == null) {
    final cred = await auth.signInAnonymously();
    user = cred.user;
  }
  return user;
});

final dioProvider = Provider<Dio>((ref) {
  final auth = ref.watch(firebaseAuthProvider);
  final dio = Dio(BaseOptions(baseUrl: kApiBaseUrl));
  dio.interceptors.add(
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        final user = auth.currentUser;
        final token = await user?.getIdToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (err, handler) {
        debugPrint(
          'Request to ${err.requestOptions.uri} failed: ${err.message}',
        );
        handler.next(err);
      },
    ),
  );
  return dio;
});

final historyQueryProvider = Provider<Query<Map<String, dynamic>>?>((ref) {
  final auth = ref.watch(firebaseAuthProvider);
  final uid = auth.currentUser?.uid;
  if (uid == null) return null;
  final firestore = ref.watch(firestoreProvider);
  return firestore
      .collection('users')
      .doc(uid)
      .collection('history')
      .orderBy('timestamp', descending: true);
});

final historyProvider = StreamProvider<List<HistoryEntry>>((ref) {
  final query = ref.watch(historyQueryProvider);
  if (query == null) return const Stream.empty();
  return query.snapshots().map(
    (snapshot) =>
        snapshot.docs.map((doc) => HistoryEntry.fromDoc(doc)).toList(),
  );
});

Future<void> saveToHistory(
  WidgetRef ref,
  String input,
  SolutionResult result, {
  String? imagePath,
  DateTime? timestamp,
}) async {
  final auth = ref.read(firebaseAuthProvider);
  final uid = auth.currentUser?.uid;
  if (uid == null) return;
  final firestore = ref.read(firestoreProvider);
  await firestore.collection('users').doc(uid).collection('history').add({
    'input': input,
    'imagePath': imagePath,
    'timestamp': timestamp ?? FieldValue.serverTimestamp(),
    'result': result.toJson(),
  });
  await cleanupHistory(ref);
}

Future<void> cleanupHistory(WidgetRef ref, {int maxEntries = 100}) async {
  final query = ref.read(historyQueryProvider);
  if (query == null) return;
  final snapshot = await query.get();
  if (snapshot.docs.length <= maxEntries) return;
  final toDelete = snapshot.docs.sublist(maxEntries);
  for (final doc in toDelete) {
    await doc.reference.delete();
  }
}
