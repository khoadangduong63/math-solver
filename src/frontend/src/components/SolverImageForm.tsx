"use client";

import { ChangeEvent, FormEvent, useRef, useState } from "react";
import { Button, Form, Image, InputGroup, Spinner } from "react-bootstrap";
import { solveImage } from "@/lib/api";
import type { ImageSolveResponse } from "@/types/api";
import { getErrorMessage } from "@/lib/errors";

export default function SolverImageForm({
  onResult,
  onError
}: {
  onResult: (r: ImageSolveResponse) => void;
  onError: (e: string | null) => void;
}) {
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) { setFile(null); setPreview(null); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    onError(null);
    if (!file) {
      onError("Please choose an image (PNG/JPG).");
      return;
    }
    setLoading(true);
    try {
      const resp = await solveImage(file);
      onResult(resp);
    } catch (err: unknown) {
      onError(getErrorMessage(err, "Image solve failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <Form.Group className="mb-2">
        <Form.Label>Upload Image</Form.Label>
        <Form.Control type="file" accept="image/*" onChange={onPick} ref={fileRef} />
      </Form.Group>
      {preview && (
        <div className="mb-2">
          <Image src={preview} alt="preview" thumbnail style={{ maxHeight: 220 }} />
        </div>
      )}
      <InputGroup className="justify-content-end">
        <Button type="submit" disabled={loading || !file}>
          {loading ? <Spinner size="sm" animation="border" /> : "Solve"}
        </Button>
      </InputGroup>
    </form>
  );
}
