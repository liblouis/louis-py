# AGENTS.md

This file provides guidance to coding agents working with code in this repository.

## Git Commit Messages

Use the Linux kernel's coding-assistants trailer format (https://docs.kernel.org/process/coding-assistants.html): `Assisted-by: <agent>:<model>`, not `Co-authored-by:`. `<agent>` is the coding agent, such as `Claude`. `<model>` is the model actually running the session.

## Project Overview

louis-py is the Python binding for [louis-rs](https://github.com/liblouis/louis-rs). The crate is `louis-rs`; its Rust library is named `louis`. louis-py is built with PyO3 and maturin as one `abi3-py311` extension, so one wheel per platform serves Python 3.11 and later.

- The API follows louis-rs's names and shapes. It is not a liblouis compatibility layer. Don't describe it, or choose values, in liblouis terms.
- louis-rs comes from crates.io as a full-version caret requirement, such as `louis-rs = "0.4.1"`. Never depend on a git `rev`.
- Each release in `CHANGELOG.md` names the louis-rs version it is built on.

## Building and Testing

```bash
# Build the extension if needed, then run all tests
uv run pytest tests

# Run one file or one test
uv run pytest tests/test_modes.py
uv run pytest tests/test_modes.py::test_name
```

`[tool.uv] cache-keys` in `pyproject.toml` makes uv rebuild the extension when `src/**/*.rs`, `Cargo.toml`, `Cargo.lock` or `pyproject.toml` change. No separate `maturin develop` step is needed.

The tests need no tables from outside the repo. `tests/conftest.py` points `LOUIS_TABLE_PATH` at `tests/tables`, which holds small fixture tables. `tests/test_tablepath.py` runs only on Windows.

### Linting

```bash
cargo fmt
cargo clippy
uv run ruff check python tests
uv run ruff format python tests
uv run ty check

# Every git hook on every file, including pytest
prek run --all-files
```

Git hooks run through prek (`prek.toml`). Clippy also runs when only `Cargo.toml` or `Cargo.lock` change.

CI (`.github/workflows/python-wheels.yml`) lints and tests. It builds wheels for five platforms and tests each one, and it builds the sdist. A published GitHub Release uploads them to PyPI through trusted publishing, in the `pypi` environment.

## Architecture

- `src/lib.rs` is the whole extension module, `louis_py._louis_py`. It defines the classes (`Translator`, `TranslationResult`, `BrailleEncoding`, `Index`, `Query`) and the exceptions `LouisError`, `TableParseError` and `TableCompileError`.
- `python/louis_py/__init__.py` re-exports the extension. It defines the enums (`Direction`, `TranslationMode`, `TableErrorKind`, `CompileErrorKind`), `EmphasisSpan` and the `TableError` dataclass in Python.
- `python/louis_py/metadata.py` re-exports `Index` and `Query` and defines `MetadataError` and its subclasses.
- `python/louis_py/_louis_py.pyi` holds the stubs and the documentation of the Rust classes. Keep it in step with `src/lib.rs`.

### The Rust and Python boundary

- The enums live in Python. Rust checks that an argument is a member of the package's enum and maps it by member name (`check_enum`, `member_name`).
- Rust builds enum members and `TableError`, and raises the metadata errors, by looking them up in the package by name (`kind_member`, `package`).
- The package is the one the extension was loaded from. `_louis_py` records it from its own module name when it loads (`PACKAGE`), and sets each class's `__module__` to it. A host can then bundle louis-py as a subpackage, such as `host.louis_py`. `tests/test_bundled.py` covers this. Never import `louis_py` by its absolute name, from Rust or inside the package.
- louis-rs marks its error enums `#[non_exhaustive]`, so a match on them needs a catch-all arm. `clippy::wildcard_enum_match_arm` is denied in `Cargo.toml`, so every known variant must be mapped explicitly. A louis-rs update that adds a variant fails clippy. The catch-all arm returns `unmapped()`, a `NotImplementedError`.
- Translation and table loading run in `py.detach`, without the GIL.
- `pyo3_log` forwards louis-rs's `log` warnings to Python's `logging`, under the `louis` logger.

## Changelog

`CHANGELOG.md` follows Keep a Changelog. cargo-release (`release.toml`) replaces `Unreleased`, `ReleaseDate`, `...HEAD` and the `<!-- next-header -->` and `<!-- next-url -->` markers. Don't use those words anywhere else in the changelog.
