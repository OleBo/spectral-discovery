# Architecture

```mermaid
flowchart TD
  A[Research Director AI] --> B[Conjecture Database]
  B --> C[Experiment Planner AI]
  C --> D[Numerical Laboratory]
  D --> E[Counterexample Search]
  E --> F[Formalization Agent]
  F --> G[Lean / Mathlib]
  E --> C
