# symgraph

Static analysis engine that maps Python codebases into a queryable property graph by resolving symbol definitions, inferring types, and tracing call/reference relationships.

## Features

*   **Symbol Extraction**: Identifies and catalogs modules, classes, functions, methods, and variables.
*   **Static Type Inference**: Performs a multi-pass analysis (up to 10 iterations) to resolve variable types and function return types across the project.
*   **Relationship Mapping**: Traces connections between symbols, specifically distinguishing between direct **calls** and symbol **references**.
*   **Context-Aware Analysis**: Handles `self` references within class scopes and resolves method calls based on inferred object types.
*   **Symbol Querying**: Provides a detailed lookup for any symbol, showing its definition location and a list of what it uses and what it is used by.

## Installation

```bash
pip install symgraph
```

## Usage

Once installed, you can use the `symgraph` command directly from your terminal.

### 1. Map an Entire Codebase
To generate a full JSON list of all edges (connections) in a directory or file:
```bash
symgraph /path/to/your/project
```
The output is a JSON array where each entry contains the source, destination, and kind of relationship (e.g., `call` or `ref`).

### 2. Inspect a Specific Symbol
To get a comprehensive report on a specific class, function, or variable:
```bash
symgraph /path/to/your/project SymbolName
```

**Example Query Result:**
```json
[
  {
    "symbol": "module.ClassName.method_name",
    "kind": "method",
    "file": "path/to/file.py",
    "lines": [10, 20],
    "uses": [
      { "name": "other_module.helper_func", "kind": "function" }
    ],
    "used_by": [
      { "name": "main.run", "kind": "function", "via": "ClassName.method_name" }
    ]
  }
]
```

## License
Apache-2.0
