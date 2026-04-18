# LangGraph Basics

## What it is
LangGraph is a graph-based workflow framework for building agentic and stateful LLM systems.

## Core concepts
- State: typed shared data carried across nodes.
- Node: a function that reads/writes state.
- Edge: routing between nodes.
- Conditional edge: choose next node based on state.

## Why useful
- Deterministic control flow.
- Better observability than monolithic agent loops.
- Easier retries and error paths.

## Practice targets
- Build one graph with success + retry + fail branches.
- Add typed state and stricter validation.
