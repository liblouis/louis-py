//! PyO3 bindings for the `louis` braille translator.
use std::path::PathBuf;

use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyValueError};
use pyo3::prelude::*;

create_exception!(
    _louis_py,
    LouisError,
    PyException,
    "Base class for louis errors."
);
create_exception!(
    _louis_py,
    TableParseError,
    LouisError,
    "Raised when a braille table fails to parse."
);
create_exception!(
    _louis_py,
    TableCompileError,
    LouisError,
    "Raised when a rule of a braille table refers to something no rule defines."
);

/// Wrap a `louis::Error` into the appropriate Python exception.
/// Re-attaches to the interpreter so it can be used directly in `.map_err`.
fn to_pyerr(err: louis::Error) -> PyErr {
    match err {
        louis::Error::Table(ref errs) => {
            let msgs: Vec<String> = errs.iter().map(ToString::to_string).collect();
            let exc = TableParseError::new_err(err.to_string());
            Python::attach(|py| {
                let _ = exc.value(py).setattr("errors", msgs);
            });
            exc
        }
        louis::Error::Compile(ref compile) => {
            let exc = TableCompileError::new_err(err.to_string());
            Python::attach(|py| {
                let value = exc.value(py);
                let _ = value.setattr("path", compile.path());
                let _ = value.setattr("line", compile.line());
            });
            exc
        }
        other => LouisError::new_err(other.to_string()),
    }
}

/// Map a raw Python `TranslationMode` bitmask to `louis::TranslationModes`.
///
/// The `table` below is the single source of truth for the Python <-> Rust mode
/// contract and must stay in sync with `TranslationMode` in
/// `python/louis_py/__init__.py`. Mapping by variant *name* (not declaration
/// order) means the bindings stay correct if louis-rs reorders the enum, and a
/// renamed/removed variant becomes a compile error here. Returns `None` if any
/// bit does not correspond to a defined mode.
fn modes_from_bits(bits: u32) -> Option<louis::TranslationModes> {
    use louis::TranslationMode::*;
    let table = [
        (1 << 0, NoContractions),
        (1 << 1, CompbrlAtCursor),
        (1 << 2, DotsIo),
        (1 << 3, CompbrlLeftCursor),
        (1 << 4, UcBrl),
        (1 << 5, NoUndefined),
        (1 << 6, PartialTrans),
    ];
    let known: u32 = table.iter().map(|(b, _)| b).sum();
    if bits & !known != 0 {
        return None;
    }
    let mut modes = louis::TranslationModes::empty();
    for (bit, mode) in table {
        if bits & bit != 0 {
            modes.insert(mode);
        }
    }
    Some(modes)
}

/// Translation direction, mirrors `louis::Direction`.
#[pyclass(eq, eq_int, from_py_object)]
#[derive(Clone, Copy, PartialEq)]
pub enum Direction {
    FORWARD = 0,
    BACKWARD = 1,
}

impl From<Direction> for louis::Direction {
    fn from(d: Direction) -> Self {
        match d {
            Direction::FORWARD => louis::Direction::Forward,
            Direction::BACKWARD => louis::Direction::Backward,
        }
    }
}

/// The result of a translation. Mirrors `louis::TranslationResult`.
#[pyclass(frozen, get_all)]
pub struct TranslationResult {
    pub output: String,
    pub emphasis: Option<Vec<(String, usize, usize)>>,
    pub output_positions: Vec<usize>,
    pub input_positions: Vec<usize>,
    pub cursor_position: Option<usize>,
}

#[pymethods]
impl TranslationResult {
    fn __repr__(&self) -> String {
        format!(
            "TranslationResult(output={:?}, emphasis={:?}, output_positions={:?}, input_positions={:?}, cursor_position={:?})",
            self.output,
            self.emphasis,
            self.output_positions,
            self.input_positions,
            self.cursor_position
        )
    }
}

impl TranslationResult {
    fn from_rust(r: &louis::TranslationResult) -> Self {
        Self {
            output: r.output().to_owned(),
            emphasis: r.emphasis().map(|emphasis| {
                emphasis
                    .spans()
                    .iter()
                    .map(|s| (s.class().to_owned(), s.range().start, s.range().end))
                    .collect()
            }),
            output_positions: r.output_positions().to_vec(),
            input_positions: r.input_positions().to_vec(),
            cursor_position: r.cursor_position(),
        }
    }
}

/// A compiled braille translator. Immutable and safe to share across threads.
#[pyclass(frozen)]
pub struct Translator {
    inner: louis::Translator,
}

#[pymethods]
impl Translator {
    /// Compile `tables`, looking each name and every `include` up in
    /// `search_path` when given, otherwise in `LOUIS_TABLE_PATH` (split on the
    /// platform separator, `.` when unset). Names are joined onto each entry in
    /// order and the first existing file wins; nothing is added to the list, so
    /// a table's own directory is searched only when listed and an absolute
    /// table name resolves against any non-empty search path.
    #[new]
    #[pyo3(signature = (tables, direction = Direction::FORWARD, *, search_path = None))]
    fn new(
        py: Python<'_>,
        tables: Vec<PathBuf>,
        direction: Direction,
        search_path: Option<Vec<PathBuf>>,
    ) -> PyResult<Self> {
        let dir: louis::Direction = direction.into();
        let inner = py
            .detach(|| match search_path {
                Some(dirs) => louis::Translator::with_search_path(&tables, dir, dirs),
                None => louis::Translator::new(&tables, dir),
            })
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }

    /// Build a translator from raw table source text. Does not resolve
    /// `include` directives.
    #[staticmethod]
    #[pyo3(signature = (table, direction = Direction::FORWARD))]
    fn from_table_source(py: Python<'_>, table: &str, direction: Direction) -> PyResult<Self> {
        let dir: louis::Direction = direction.into();
        let inner = py
            .detach(|| louis::Translator::from_table_source(table, dir))
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }

    /// Translate `text`.
    fn translate(&self, py: Python<'_>, text: &str) -> String {
        py.detach(|| self.inner.translate(text))
    }

    /// Translate `text` with options, and report which input became which output.
    #[pyo3(signature = (text, *, mode = 0, emphasis = None, cursor_position = None))]
    fn translate_with_options(
        &self,
        py: Python<'_>,
        text: &str,
        mode: u32,
        emphasis: Option<Vec<(String, usize, usize)>>,
        cursor_position: Option<usize>,
    ) -> PyResult<TranslationResult> {
        let modes = modes_from_bits(mode).ok_or_else(|| {
            PyValueError::new_err(format!("invalid translation mode bits: {mode:#x}"))
        })?;
        let mut options = louis::TranslationOptions::default().with_modes(modes);
        if let Some(spans) = emphasis {
            let emphasis: louis::Emphasis = spans
                .into_iter()
                .map(|(class, start, end)| louis::EmphasisSpan::new(class, start..end))
                .collect();
            options = options.with_emphasis(emphasis);
        }
        if let Some(position) = cursor_position {
            options = options.with_cursor_position(position);
        }
        let result = py.detach(|| self.inner.translate_with_options(text, &options));
        Ok(TranslationResult::from_rust(&result))
    }
}

/// The `_louis_py` extension module. Public API lives in the `louis_py`
/// Python package, which re-exports from here.
#[pymodule]
fn _louis_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let py = m.py();
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add_class::<Direction>()?;
    m.add_class::<Translator>()?;
    m.add_class::<TranslationResult>()?;
    m.add("LouisError", py.get_type::<LouisError>())?;
    m.add("TableParseError", py.get_type::<TableParseError>())?;
    m.add("TableCompileError", py.get_type::<TableCompileError>())?;
    Ok(())
}
