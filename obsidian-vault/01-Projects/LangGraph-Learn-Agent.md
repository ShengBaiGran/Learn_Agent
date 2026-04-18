# LangGraph Learn Agent

## Objective
Build a learning project for LLM + LangGraph + test workflow automation.

## Current implementation notes
- Entry point: `main.py`
- Graph module: `py_code/modbus_test_graph.py`
- LLM/tools module: `py_code/agent.py`

## Current flow
- Parse user intent and parameters.
- Run graph: write -> wait -> read -> validate.
- Retry when validation fails until retry limit.

## Improvement backlog
- Add stronger typing for model response handling.
- Improve prompt format so parser stability is higher.
- Separate mock Modbus layer from real driver layer.
- Add tests for graph routing behavior.

## This week focus
- Stabilize type hints and lint baseline.
- Add one test per graph branch.
