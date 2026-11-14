//! PyO3 bindings for the `louis` braille translator.
use std::path::PathBuf;
use std::sync::OnceLock;

use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyTypeError, PyValueError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyString, PyTuple};
use search_path::SearchPath;

create_exception!(
    louis_py,
    LouisError,
    PyException,
    "Base class for louis errors."
);
create_exception!(
    louis_py,
    TableParseError,
    LouisError,
    "Raised when a braille table fails to parse."
);
create_exception!(
    louis_py,
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

/// The package this module was loaded from.
static PACKAGE: OnceLock<String> = OnceLock::new();

/// Check that `obj` is a member of the enum `class` of the package this module was
/// loaded from, raising `TypeError` otherwise.
fn check_enum(obj: &Bound<'_, PyAny>, class: &str) -> PyResult<()> {
    let package = PACKAGE.get().expect("set when the module is initialized");
    let expected = obj.py().import(package)?.getattr(class)?;
    if obj.is_instance(&expected)? {
        Ok(())
    } else {
        Err(PyTypeError::new_err(format!(
            "expected {package}.{class}, not {}",
            obj.get_type().name()?
        )))
    }
}

/// The name of the enum member `member`.
fn member_name(member: &Bound<'_, PyAny>) -> PyResult<String> {
    member.getattr(intern!(member.py(), "name"))?.extract()
}

/// A `louis_py.Direction`, as the `louis::Direction` it names.
struct Direction(louis::Direction);

impl Direction {
    const FORWARD: Self = Self(louis::Direction::Forward);
}

impl<'a, 'py> FromPyObject<'a, 'py> for Direction {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        check_enum(&obj, "Direction")?;
        match member_name(&obj)?.as_str() {
            "FORWARD" => Ok(Self(louis::Direction::Forward)),
            "BACKWARD" => Ok(Self(louis::Direction::Backward)),
            name => Err(PyValueError::new_err(format!(
                "louis_py.Direction.{name} has no louis-rs counterpart"
            ))),
        }
    }
}

/// A `louis_py.TranslationMode`, as the `louis::TranslationModes` its members
/// name.
#[derive(Default)]
struct Modes(louis::TranslationModes);

impl<'a, 'py> FromPyObject<'a, 'py> for Modes {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> PyResult<Self> {
        use louis::TranslationMode::*;
        check_enum(&obj, "TranslationMode")?;
        let mut modes = louis::TranslationModes::empty();
        for member in obj.try_iter()? {
            modes.insert(match member_name(&member?)?.as_str() {
                "NO_CONTRACTIONS" => NoContractions,
                "COMPBRL_AT_CURSOR" => CompbrlAtCursor,
                "COMPBRL_LEFT_CURSOR" => CompbrlLeftCursor,
                "NO_UNDEFINED" => NoUndefined,
                "PARTIAL_TRANS" => PartialTrans,
                name => {
                    return Err(PyValueError::new_err(format!(
                        "louis_py.TranslationMode.{name} has no louis-rs counterpart"
                    )));
                }
            });
        }
        Ok(Self(modes))
    }
}

/// The result of a translation. Mirrors `louis::TranslationResult`, with each
/// field converted to a Python object once, so that reading an attribute
/// returns that object instead of converting the field again.
#[pyclass(frozen, get_all, module = "louis_py")]
pub struct TranslationResult {
    pub output: Py<PyString>,
    pub emphasis: Option<Py<PyTuple>>,
    pub output_positions: Py<PyTuple>,
    pub input_positions: Py<PyTuple>,
    pub cursor_position: Option<usize>,
}

#[pymethods]
impl TranslationResult {
    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        Ok(format!(
            "TranslationResult(output={}, emphasis={}, output_positions={}, input_positions={}, cursor_position={})",
            self.output.bind(py).repr()?,
            (&self.emphasis).into_pyobject(py)?.repr()?,
            self.output_positions.bind(py).repr()?,
            self.input_positions.bind(py).repr()?,
            self.cursor_position.into_pyobject(py)?.repr()?,
        ))
    }
}

impl TranslationResult {
    fn from_rust(py: Python<'_>, r: &louis::TranslationResult) -> PyResult<Self> {
        let emphasis = r
            .emphasis()
            .map(|emphasis| {
                PyTuple::new(
                    py,
                    emphasis
                        .spans()
                        .iter()
                        .map(|s| (s.class(), s.range().start, s.range().end)),
                )
            })
            .transpose()?;
        Ok(Self {
            output: PyString::new(py, r.output()).unbind(),
            emphasis: emphasis.map(Bound::unbind),
            output_positions: PyTuple::new(py, r.output_positions())?.unbind(),
            input_positions: PyTuple::new(py, r.input_positions())?.unbind(),
            cursor_position: r.cursor_position(),
        })
    }
}

/// `search_path`, or when it is `None` the directories in `LOUIS_TABLE_PATH`,
/// read as louis-rs reads them. louis-rs would read the variable itself after
/// the interpreter is released, while another Python thread may be changing the
/// environment; reading it here, while attached, rules that out.
fn search_path_or_table_path(search_path: Option<Vec<PathBuf>>) -> Vec<PathBuf> {
    search_path.unwrap_or_else(|| SearchPath::new_or("LOUIS_TABLE_PATH", ".").into())
}

/// Which characters stand for the braille cells, such as ASCII braille,
/// loaded from a liblouis display table (`.dis`). Immutable and safe to share
/// across threads; one encoding can serve translators in both directions.
#[pyclass(frozen, module = "louis_py")]
pub struct BrailleEncoding {
    inner: louis::BrailleEncoding,
}

#[pymethods]
impl BrailleEncoding {
    /// Load the display table `table`, looking it and every `include` up in
    /// `search_path` when given, otherwise in `LOUIS_TABLE_PATH`, as
    /// `Translator` does.
    #[new]
    #[pyo3(signature = (table, *, search_path = None))]
    fn new(py: Python<'_>, table: PathBuf, search_path: Option<Vec<PathBuf>>) -> PyResult<Self> {
        let search_path = search_path_or_table_path(search_path);
        let inner = py
            .detach(|| louis::BrailleEncoding::with_search_path(&table, search_path))
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }

    /// Build an encoding from raw display table source text. Does not resolve
    /// `include` directives.
    #[staticmethod]
    fn from_table_source(py: Python<'_>, table: &str) -> PyResult<Self> {
        let inner = py
            .detach(|| louis::BrailleEncoding::from_table_source(table))
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }
}

/// `translator`, reading and writing braille in `encoding` when one is given.
fn encoded(
    translator: louis::Translator,
    encoding: Option<&louis::BrailleEncoding>,
) -> louis::Translator {
    match encoding {
        Some(encoding) => translator.with_braille_encoding(encoding),
        None => translator,
    }
}

/// A compiled braille translator. Immutable and safe to share across threads.
#[pyclass(frozen, module = "louis_py")]
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
    /// table name resolves against any non-empty search path. Braille is read
    /// and written in `braille_encoding` when given, otherwise as Unicode
    /// braille.
    #[new]
    #[pyo3(signature = (
        tables,
        direction = Direction::FORWARD,
        *,
        search_path = None,
        braille_encoding = None,
    ))]
    fn new(
        py: Python<'_>,
        tables: Vec<PathBuf>,
        direction: Direction,
        search_path: Option<Vec<PathBuf>>,
        braille_encoding: Option<Bound<'_, BrailleEncoding>>,
    ) -> PyResult<Self> {
        let Direction(dir) = direction;
        let encoding = braille_encoding.as_ref().map(|e| &e.get().inner);
        let search_path = search_path_or_table_path(search_path);
        let inner = py
            .detach(|| {
                louis::Translator::with_search_path(&tables, dir, search_path)
                    .map(|translator| encoded(translator, encoding))
            })
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }

    /// Build a translator from raw table source text. Does not resolve
    /// `include` directives.
    #[staticmethod]
    #[pyo3(signature = (table, direction = Direction::FORWARD, *, braille_encoding = None))]
    fn from_table_source(
        py: Python<'_>,
        table: &str,
        direction: Direction,
        braille_encoding: Option<Bound<'_, BrailleEncoding>>,
    ) -> PyResult<Self> {
        let Direction(dir) = direction;
        let encoding = braille_encoding.as_ref().map(|e| &e.get().inner);
        let inner = py
            .detach(|| {
                louis::Translator::from_table_source(table, dir)
                    .map(|translator| encoded(translator, encoding))
            })
            .map_err(to_pyerr)?;
        Ok(Self { inner })
    }

    /// The emphasis classes the tables declare with `emphclass`, such as
    /// `italic` or `bold`, in the order they declare them: the class names
    /// emphasis spans can use.
    #[getter]
    fn emphasis_classes(&self) -> Vec<String> {
        self.inner
            .emphasis_classes()
            .map(ToOwned::to_owned)
            .collect()
    }

    /// Translate `text`.
    fn translate(&self, py: Python<'_>, text: &str) -> String {
        py.detach(|| self.inner.translate(text))
    }

    /// Translate `text` with options, and report which input became which output.
    #[pyo3(signature = (text, *, mode = Modes::default(), emphasis = None, cursor_position = None))]
    fn translate_with_options(
        &self,
        py: Python<'_>,
        text: &str,
        mode: Modes,
        emphasis: Option<Vec<(String, usize, usize)>>,
        cursor_position: Option<usize>,
    ) -> PyResult<TranslationResult> {
        let mut options = louis::TranslationOptions::default().with_modes(mode.0);
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
        TranslationResult::from_rust(py, &result)
    }
}

/// The `_louis_py` extension module. Public API lives in the `louis_py`
/// Python package, which re-exports from here.
#[pymodule]
fn _louis_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let py = m.py();
    let name = m.name()?;
    let name = name.to_cow()?;
    let package = name
        .rsplit_once('.')
        .map_or("louis_py", |(package, _)| package);
    let _ = PACKAGE.set(package.to_owned());
    let _ = pyo3_log::Logger::new(py, pyo3_log::Caching::Nothing)?.install();
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    let types = [
        py.get_type::<BrailleEncoding>(),
        py.get_type::<Translator>(),
        py.get_type::<TranslationResult>(),
        py.get_type::<LouisError>(),
        py.get_type::<TableParseError>(),
        py.get_type::<TableCompileError>(),
    ];
    for class in types {
        // The package re-exports these types, so name it as their module, which
        // pickling imports to find them again. It is `louis_py` unless a host
        // bundles the package as a subpackage of its own.
        class.setattr(intern!(py, "__module__"), package)?;
        m.add(class.name()?, class)?;
    }
    Ok(())
}
