"use client";

import { Accordion } from "react-bootstrap";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import type { Step } from "@/types/api";

export default function StepsList({ steps }: { steps: Step[] }) {
  if (!steps?.length) return null;
  return (
    <Accordion alwaysOpen>
      {steps.map((st, idx) => (
        <Accordion.Item eventKey={String(idx)} key={idx}>
          <Accordion.Header>{st.title || `Step ${idx + 1}`}</Accordion.Header>
          <Accordion.Body>
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {st.explanation || ""}
            </ReactMarkdown>
          </Accordion.Body>
        </Accordion.Item>
      ))}
    </Accordion>
  );
}
