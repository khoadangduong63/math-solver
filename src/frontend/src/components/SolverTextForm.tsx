"use client";

import { FormEvent, useRef, useState } from "react";
import { Button, Form, InputGroup, Spinner } from "react-bootstrap";
import { solveText } from "@/lib/api";
import type { SolveResponse } from "@/types/api";
import { getErrorMessage } from "@/lib/errors";

export default function SolverTextForm({
  onResult,
  onError
}: {
  onResult: (r: SolveResponse) => void;
  onError: (e: string | null) => void;
}) {
  const questionRef = useRef<HTMLTextAreaElement | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    onError(null);
    const question = questionRef.current?.value?.trim() || "";
    if (!question) {
      onError("Please enter a math question.");
      return;
    }
    setLoading(true);
    try {
      const resp = await solveText({ question, level: "auto", locale: "en" });
      onResult(resp);
    } catch (err: unknown) {
      onError(getErrorMessage(err, "Solve failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <Form.Group className="mb-2">
        <Form.Label>Question</Form.Label>
        <Form.Control as="textarea" rows={5} ref={questionRef} placeholder="e.g. Solve (x-1)/2 = 1" />
      </Form.Group>
      <InputGroup className="justify-content-end">
        <Button type="submit" disabled={loading}>
          {loading ? <Spinner size="sm" animation="border" /> : "Solve"}
        </Button>
      </InputGroup>
    </form>
  );
}
