export type Step = {
  title: string;
  explanation: string;
};

export type ModelInfo = {
  provider: string;
  name: string;
};

export type SolveResponse = {
  final_answer: string;
  steps: Step[];
  verified: boolean;
  latex?: string | null;
  level?: string | null;
  confidence?: number | null;
  difficulty?: number | null;
  model?: ModelInfo | null;
};

export type ImageSolveResponse = {
  ocr_text: string;
  result: SolveResponse;
};

export type TextSolveRequest = {
  question: string;
  level?: string;
  locale?: string;
};
