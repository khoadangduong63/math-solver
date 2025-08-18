"use client";

import { Badge, Card, ListGroup, ProgressBar } from "react-bootstrap";
import StepsList from "./StepsList";
import type { SolveResponse } from "@/types/api";

function ConfidenceBar({ value }: { value: number | null | undefined }) {
  if (value == null) return null;
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="mt-2">
      <small className="text-muted">Confidence</small>
      <ProgressBar now={pct} label={`${pct}%`} />
    </div>
  );
}

export default function ResultCard({
  title,
  result,
  ocrText
}: {
  title: string;
  result: SolveResponse;
  ocrText: string | null;
}) {
  return (
    <Card>
      <Card.Header className="d-flex justify-content-between align-items-center">
        <span><strong>{title}</strong></span>
        <span>
          {result.verified ? (
            <Badge bg="success" className="badge-verified">Verified</Badge>
          ) : (
            <Badge bg="secondary" className="badge-unverified">Unverified</Badge>
          )}
        </span>
      </Card.Header>
      <Card.Body>
        <ListGroup variant="flush" className="mb-3">
          <ListGroup.Item>
            <strong>Final Answer:</strong> {result.final_answer || <em>(empty)</em>}
          </ListGroup.Item>
          {result.model && (
            <ListGroup.Item>
              <strong>Model:</strong> {result.model.provider} / {result.model.name}
            </ListGroup.Item>
          )}
          {typeof result.difficulty === "number" && (
            <ListGroup.Item>
              <strong>Difficulty:</strong> {result.difficulty}
            </ListGroup.Item>
          )}
          {ocrText && (
            <ListGroup.Item>
              <strong>OCR Hint:</strong> <span className="text-muted">{ocrText}</span>
            </ListGroup.Item>
          )}
        </ListGroup>

        <ConfidenceBar value={result.confidence ?? null} />
        <hr />
        <StepsList steps={result.steps || []} />
      </Card.Body>
    </Card>
  );
}
