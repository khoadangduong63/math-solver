"use client";

import { Container, Navbar } from "react-bootstrap";

export default function Header() {
  return (
    <Navbar bg="dark" data-bs-theme="dark" className="mb-4">
      <Container>
        <Navbar.Brand style={{ color: "white" }}>
          <strong>Math Solver</strong>
        </Navbar.Brand>
      </Container>
    </Navbar>
  );
}
