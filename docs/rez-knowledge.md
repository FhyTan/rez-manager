# Rez for AI Coding Context

This document is an AI-focused context guide for Rez.
It helps an AI assistant generate correct Python and CLI usage with lower hallucination risk.

## 1) Purpose and Boundaries

### Purpose

- Provide a compact mental model of Rez.
- Provide high-frequency command intent (not full parameter details).
- Provide minimal and practical Python usage patterns.
- Provide official links for deeper lookup.

### In Scope

- Core concepts.
- Common commands.
- Common configuration concerns.
- Common Python statements and integration patterns.

### Out of Scope

- Complete CLI parameter reference.
- Complete Python API reference.
- Internal implementation details of the solver.

## 2) What Rez Is

Rez is a cross-platform package manager centered on dynamic environment resolution.

Key difference from many package managers:

- Traditional approach: install dependencies into each environment instance.
- Rez approach: store package versions in central repositories, then resolve and compose environments from package requests.

Practical impact:

- Environment creation is usually fast.
- Multiple projects can reuse the same package artifacts.
- Dependency resolution is explicit and reproducible (when requests and repositories are controlled).

## 3) Core Concepts (AI-Oriented)

### Package Request

- A user asks for packages, often with optional version constraints.
- AI rule: treat request strings as solver input, not as import paths.

### Resolve / Solver

- Rez computes a compatible set of package versions from requests plus dependencies.
- AI rule: do not manually "guess" transitive dependencies if Rez can resolve them.

### Context

- A resolved environment definition that can be inspected or activated.
- AI rule: prefer operating on a context rather than mutating global environment state directly.

### Package Repository

- Central locations where package definitions/versions are discovered.
- AI rule: if behavior differs across machines, check repository and config first.

### Variant

- A package can provide multiple build/runtime variants for different platforms or dependency sets.
- AI rule: resolution mismatches are often variant- or platform-related, not only version-related.

## 4) Common Command Intent (No Parameter Deep Dive)

Use commands by purpose:

- Environment/session: `rez-env`, `rez-context`, `rez-status`
- Discover/search: `rez-search`, `rez-help`, `rez-view`
- Build/release flow: `rez-build`, `rez-test`, `rez-release`
- Config/debug: `rez-config`, `rez-diff`, `rez-depends`

AI rule:

- Pick commands by lifecycle step (discover -> resolve -> validate -> release), not by memorizing all flags.

## 5) Configuration Model (Practical)

When troubleshooting, prioritize these dimensions:

- Package search paths / repository locations.
- Caching behavior.
- Resolve behavior influenced by local/project/global settings.

AI checklist before concluding "code is wrong":

1. Confirm active config values.
2. Confirm package repositories are reachable and expected.
3. Confirm current shell/context is the one being debugged.

## 6) Python Usage Patterns (Minimal, High-Confidence)

Below are practical patterns for generating reliable Python code around Rez.

### Pattern A: Use Rez CLI from Python (Most Stable Integration)

Use this when you need robust automation and low API-surface risk.

```python
import json
import subprocess
from typing import Sequence


def run_rez_context(packages: Sequence[str]) -> dict:
    """Resolve packages via rez CLI and return parsed context output.

    Note: the exact output format depends on your command/options.
    Keep this wrapper small and validate output in your environment.
    """
    cmd = ["rez-context", *packages]
    completed = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )

    # If you choose a JSON-producing command/option in your environment,
    # parse it here. Otherwise keep stdout as raw text.
    return {"stdout": completed.stdout, "stderr": completed.stderr}
```

Why this is safe:

- CLI contracts are often more stable for automation than deep in-process API usage.
- Easy to log and debug command-level failures.

### Pattern B: In-Process Resolve Context (When You Need Python Objects)

Use this when your project intentionally depends on Rez Python internals.

```python
from rez.resolved_context import ResolvedContext


def create_context(package_requests: list[str]) -> ResolvedContext:
    """Create a resolved context from package requests."""
    ctx = ResolvedContext(package_requests)
    return ctx
```

Practical notes:

- Keep usage thin and isolated in one adapter module.
- Pin Rez version for reproducible behavior.
- Validate methods/properties against the official API page for your version.

### Pattern C: Defensive Wrapper for AI-Generated Code

Use this to reduce brittle assumptions and surface actionable errors.

```python
import subprocess


def safe_rez_call(args: list[str]) -> tuple[int, str, str]:
    """Execute rez command and return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr
```

AI rule:

- Never assume success; always inspect return code and stderr.

## 7) Anti-Hallucination Rules for AI

1. Do not invent module paths, classes, or methods.
2. If uncertain, choose CLI-based integration first.
3. Keep Rez-facing code in a dedicated adapter layer.
4. Pin and record Rez version used by the project.
5. For unresolved calls, consult official index links before coding deeper.

Common failure patterns:

- Treating package request strings as Python import statements.
- Assuming dependency layout instead of letting Rez resolve it.
- Mixing shell context from one session with commands from another.

## 8) Official Link Gateway (Use for Deep Lookup)

- Documentation home: https://rez.readthedocs.io/en/stable/
- Basic concepts: https://rez.readthedocs.io/en/stable/basic_concepts.html
- Context: https://rez.readthedocs.io/en/stable/context.html
- Configuring Rez: https://rez.readthedocs.io/en/stable/configuring_rez.html
- Commands index: https://rez.readthedocs.io/en/stable/commands_index.html
- Python API index: https://rez.readthedocs.io/en/stable/api.html
- Environment variables: https://rez.readthedocs.io/en/stable/environment.html

## 9) Glossary and Retrieval Keywords

### Glossary

- Package request: user-specified package constraints for resolution.
- Resolve: process of selecting compatible package versions.
- Context: resolved environment description used for shell/runtime setup.
- Repository: location containing package definitions and versions.
- Variant: package flavor for platform/dependency differences.

### Retrieval Keywords

- rez resolved context python
- rez package request version constraints
- rez commands index env context
- rez configuring repositories cache
- rez python api resolved_context
