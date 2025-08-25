import 'dart:convert';

class SolutionStep {
  final String title;
  final String explanation;
  final String? latex;

  SolutionStep({
    required this.title,
    required this.explanation,
    this.latex,
  });

  factory SolutionStep.fromJson(dynamic json) {
    if (json is Map<String, dynamic>) {
      return SolutionStep(
        title: json['title']?.toString() ?? '',
        explanation: json['explanation']?.toString() ??
            json['description']?.toString() ??
            '',
        latex: json['latex']?.toString(),
      );
    }
    return SolutionStep(title: '', explanation: json?.toString() ?? '');
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'title': title,
      'explanation': explanation,
    };
    if (latex != null) map['latex'] = latex;
    return map;
  }
}

class SolutionResult {
  final String finalAnswer;
  final String latex;
  final List<SolutionStep> steps;
  final String? ocrText;
  final bool? verified;
  final int? confidence;
  final int? difficulty;
  final String? level;
  final Map<String, dynamic>? model;
  final Map<String, dynamic> raw;

  SolutionResult({
    required this.finalAnswer,
    required this.latex,
    required this.steps,
    required this.raw,
    this.ocrText,
    this.verified,
    this.confidence,
    this.difficulty,
    this.level,
    this.model,
  });

  factory SolutionResult.fromJson(Map<String, dynamic> json) {
    final raw = Map<String, dynamic>.from(json);

    final core = json['result'] is Map<String, dynamic>
        ? json['result'] as Map<String, dynamic>
        : json;

    final fa = core['final_answer'] ??
        core['finalAnswer'] ??
        json['final_answer'] ??
        json['finalAnswer'] ??
        '';

    final latex =
        core['latex']?.toString() ?? json['latex']?.toString() ?? '';

    final stepsJson = core['steps'] as List<dynamic>? ?? [];
    final steps = stepsJson.map((e) => SolutionStep.fromJson(e)).toList();

    return SolutionResult(
      finalAnswer: fa.toString(),
      latex: latex,
      steps: steps,
      raw: raw,
      ocrText: json['ocr_text']?.toString(),
      verified: json['verified'] is bool
          ? json['verified'] as bool
          : (json['verified'] == null
              ? null
              : json['verified'].toString().toLowerCase() == 'true'),
      confidence: (json['confidence'] as num?)?.toInt(),
      difficulty: (json['difficulty'] as num?)?.toInt(),
      level: json['level']?.toString(),
      model: json['model'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['model'] as Map)
          : null,
    );
  }

  Map<String, dynamic> toJson() => raw;

  String toRawJson() => const JsonEncoder.withIndent('  ').convert(toJson());
}
