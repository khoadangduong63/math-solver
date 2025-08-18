"use client";

import { useState } from "react";
import { Alert, Col, Row, Tab, Tabs } from "react-bootstrap";
import SolverTextForm from "@/components/SolverTextForm";
import SolverImageForm from "@/components/SolverImageForm";
import ResultCard from "@/components/ResultCard";
import type { SolveResponse, ImageSolveResponse } from "@/types/api";

export default function Page() {
  const [error, setError] = useState<string | null>(null);
  const [textResult, setTextResult] = useState<SolveResponse | null>(null);
  const [imageResult, setImageResult] = useState<ImageSolveResponse | null>(null);

  return (
    <Row>
      <Col lg={6}>
        <Tabs defaultActiveKey="text" className="mb-3">
          <Tab eventKey="text" title="Solve by Text">
            <SolverTextForm
              onError={setError}
              onResult={(r) => { setTextResult(r); setImageResult(null); }}
            />
          </Tab>
          <Tab eventKey="image" title="Solve by Image">
            <SolverImageForm
              onError={setError}
              onResult={(r) => { setImageResult(r); setTextResult(null); }}
            />
          </Tab>
        </Tabs>
        {error && <Alert variant="danger" onClose={() => setError(null)} dismissible>{error}</Alert>}
      </Col>

      <Col lg={6}>
        {textResult && (
          <ResultCard title="Text Solution" result={textResult} ocrText={null} />
        )}
        {imageResult && (
          <ResultCard title="Image Solution" result={imageResult.result} ocrText={imageResult.ocr_text || null} />
        )}
        {!textResult && !imageResult && (
          <Alert variant="secondary">Results will appear here.</Alert>
        )}
      </Col>
    </Row>
  );
}
