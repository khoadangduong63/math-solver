import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:dio/dio.dart';
import 'package:go_router/go_router.dart';

import '../models/solution_result.dart';
import '../providers.dart';

class ImageSolvePage extends ConsumerStatefulWidget {
  const ImageSolvePage({super.key});

  @override
  ConsumerState<ImageSolvePage> createState() => _ImageSolvePageState();
}

class _ImageSolvePageState extends ConsumerState<ImageSolvePage> {
  bool _loading = false;

  Future<void> _pick() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery);
    if (picked == null) return;
    setState(() => _loading = true);
    try {
      final bytes = await picked.readAsBytes();
      final compressed = await FlutterImageCompress.compressWithList(
        bytes,
        quality: 70,
      );
      final dio = ref.read(dioProvider);
      final form = FormData.fromMap({
        'file': MultipartFile.fromBytes(compressed, filename: 'image.jpg'),
      });
      final res = await dio.post('/solve-image', data: form);
      final result = SolutionResult.fromJson(res.data as Map<String, dynamic>);
      final timestamp = DateTime.now();
      await saveToHistory(ref, result.ocrText ?? '[image]', result,
          imagePath: picked.path, timestamp: timestamp);
      if (mounted) {
        context.push(
          '/solution',
          extra: {
            'result': result,
            'question': result.ocrText,
            'imagePath': picked.path,
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
      appBar: AppBar(title: const Text('Image Solve')),
      body: Column(
        children: [
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _loading ? null : _pick,
            child: _loading
                ? const CircularProgressIndicator()
                : const Text('Pick Image'),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}
