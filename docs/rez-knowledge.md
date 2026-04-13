# Rez for AI Coding Context

This document is an AI-focused context guide for Rez.
It helps an AI assistant generate correct Python API usage and Rez terminology with lower
hallucination risk.

## 1) Purpose and Boundaries

### Purpose

- Provide a compact mental model of Rez.
- Provide high-frequency Rez terminology for docs lookup.
- Provide minimal and practical Python API usage patterns.
- Provide official links for deeper lookup.

### In Scope

- Core concepts.
- Common terminology seen in official Rez docs.
- Common configuration concerns.
- Common Python API statements and integration patterns.

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

## 4) CLI Name Mapping (Reference Only)

These names are useful when reading official docs or translating user terminology, but this app
must not execute `rez-*` commands via `subprocess`.

Treat common CLI names as API lookup hints:

- `rez-env`, `rez-context`, `rez-status` -> think `ResolvedContext` creation, loading, and
  inspection.
- `rez-search`, `rez-view` -> think repository/package queries from the Rez Python API.
- `rez-config`, `rez-diff`, `rez-depends` -> think configuration and dependency inspection concepts,
  not app runtime integration points.
- `rez-build`, `rez-test`, `rez-release` -> packaging pipeline terms; usually out of scope for this
  GUI app runtime.

AI rule:

- Use CLI names only as documentation vocabulary. Application code should stay inside the Rez
  Python API and adapter layer.

## 5) Configuration Model (Practical)

When troubleshooting, prioritize these dimensions:

- Package search paths / repository locations.
- Caching behavior.
- Resolve behavior influenced by local/project/global settings.

AI checklist before concluding "code is wrong":

1. Confirm active config values.
2. Confirm package repositories are reachable and expected.
3. Confirm the in-process context or loaded `.rxt` is the one being debugged.

## 6) Python Usage Patterns (Minimal, High-Confidence)

Below are practical patterns for generating reliable Python code around Rez.

### Pattern A: In-Process Resolve Context (Default for this app)

Use this as the default integration pattern in `rez-manager`.

```python
from rez.resolved_context import ResolvedContext


def create_context(package_requests: list[str]) -> ResolvedContext:
    """Create a resolved context from package requests."""
    return ResolvedContext(package_requests)
```

Why this is safe:

- Matches this app's architecture: Rez access stays in a thin Python adapter layer.
- Does not depend on `rez-*` executables being present on `PATH`.
- Works with Rez installed as an importable Python package in the app environment.

### Pattern B: Inspect or Persist the Context In-Process

Use this when the UI needs resolved packages, environment variables, tools, or a serialized `.rxt`
file.

```python
from rez.resolved_context import ResolvedContext


def summarize_context(package_requests: list[str]) -> dict[str, object]:
    ctx = ResolvedContext(package_requests)
    return {
        "packages": [str(pkg) for pkg in ctx.resolved_packages],
        "environ": dict(ctx.get_environ()),
        "tools": list(ctx.get_tools().keys()),
    }


def save_context(package_requests: list[str], path: str) -> None:
    ctx = ResolvedContext(package_requests)
    ctx.save(path)


def load_context(path: str) -> ResolvedContext:
    return ResolvedContext.load(path)
```

Practical notes:

- Keep usage thin and isolated in one adapter module.
- Pin Rez version for reproducible behavior.
- Validate methods/properties against the official API page for your version.

### Pattern C: Thin Adapter Wrapper with Structured Errors

Use this to keep QML/UI code away from Rez internals while surfacing actionable failures.

```python
from dataclasses import dataclass

from rez.resolved_context import ResolvedContext


@dataclass
class ResolveResult:
    success: bool
    packages: list[str]
    environ: dict[str, str]
    tools: list[str]
    error: str | None = None


def resolve_context(package_requests: list[str]) -> ResolveResult:
    try:
        ctx = ResolvedContext(package_requests)
        return ResolveResult(
            success=True,
            packages=[str(pkg) for pkg in ctx.resolved_packages],
            environ=dict(ctx.get_environ()),
            tools=list(ctx.get_tools().keys()),
        )
    except Exception as exc:
        return ResolveResult(
            success=False,
            packages=[],
            environ={},
            tools=[],
            error=str(exc),
        )
```

AI rule:

- Never assume success; always surface resolve errors explicitly to the caller.
- Do not shell out to `rez-env`, `rez-context`, or other `rez-*` commands from app code.

## 7) Anti-Hallucination Rules for AI

1. Do not invent module paths, classes, or methods.
2. Prefer documented Python API entry points such as `rez.resolved_context.ResolvedContext`.
3. Keep Rez-facing code in a dedicated adapter layer.
4. Do not call `rez-*` executables from the app with `subprocess`.
5. Do not depend on an external Rez installation outside the Python environment used by the app.
6. Pin and record Rez version used by the project.
7. For unresolved calls, consult official index links before coding deeper.

Common failure patterns:

- Treating package request strings as Python import statements.
- Assuming dependency layout instead of letting Rez resolve it.
- Mixing app state with assumptions about an external shell session or CLI context.

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
