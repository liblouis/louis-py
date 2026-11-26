//! PyO3 bindings for the `louis` braille translator.
use std::path::{Path, PathBuf};
use std::sync::OnceLock;

use pyo3::create_exception;
use pyo3::exceptions::{
    PyBaseException, PyException, PyNotImplementedError, PyTypeError, PyValueError,
};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyMapping, PyString, PyTuple};
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
    Python::attach(|py| louis_exception(py, &err).unwrap_or_else(|failure| failure))
}

/// `err` as the appropriate Python exception.
fn louis_exception(py: Python<'_>, err: &louis::Error) -> PyResult<PyErr> {
    match err {
        louis::Error::Table(errors) => {
            let errors = errors
                .iter()
                .map(|error| table_error(py, error))
                .collect::<PyResult<Vec<_>>>()?;
            let exc = TableParseError::new_err(err.to_string());
            exc.value(py).setattr(intern!(py, "errors"), errors)?;
            Ok(exc)
        }
        louis::Error::Compile(compile) => {
            let exc = TableCompileError::new_err(err.to_string());
            let value = exc.value(py);
            value.setattr(intern!(py, "path"), compile.path())?;
            value.setattr(intern!(py, "line"), compile.line())?;
            set_compile_error_kind(value, compile.kind())?;
            Ok(exc)
        }
        _ => Ok(LouisError::new_err(err.to_string())),
    }
}

/// `error` as a `louis_py.TableError`.
fn table_error<'py>(py: Python<'py>, error: &louis::TableError) -> PyResult<Bound<'py, PyAny>> {
    use louis::TableError::*;
    let fields = PyDict::new(py);
    if let Syntax {
        path: Some(path), ..
    }
    | NotReadable { path, .. }
    | NotFound(path)
    | HyphenationNotFound(path)
    | HyphenationNotReadable { path, .. }
    | HyphenationSyntax { path, .. } = error
    {
        fields.set_item("path", path)?;
    }
    let kind = match error {
        Syntax { line, .. } => {
            fields.set_item("line", line)?;
            "SYNTAX"
        }
        IncludesNotSupportedInMemory => "INCLUDES_NOT_SUPPORTED_IN_MEMORY",
        NotReadable { .. } => "NOT_READABLE",
        NotFound(_) => "NOT_FOUND",
        HyphenationNotFound(_) => "HYPHENATION_NOT_FOUND",
        HyphenationNotReadable { .. } => "HYPHENATION_NOT_READABLE",
        HyphenationSyntax { .. } => "HYPHENATION_SYNTAX",
        CircularInclude(paths) => {
            fields.set_item("paths", PyTuple::new(py, paths)?)?;
            "CIRCULAR_INCLUDE"
        }
        IncludeTooDeep(depth) => {
            fields.set_item("depth", depth)?;
            "INCLUDE_TOO_DEEP"
        }
        ConflictingEndmodephrasePosition(emphasis_class) => {
            fields.set_item("emphasis_class", emphasis_class)?;
            "CONFLICTING_ENDMODEPHRASE_POSITION"
        }
        ConflictingEndcapsphrasePosition => "CONFLICTING_ENDCAPSPHRASE_POSITION",
        _ => return Err(unmapped(error)),
    };
    fields.set_item("kind", kind_member(py, "TableErrorKind", kind)?)?;
    fields.set_item("message", error.to_string())?;
    package(py)?.getattr("TableError")?.call((), Some(&fields))
}

/// Set `kind` and the attributes of `kind` on the `TableCompileError` `exc`.
fn set_compile_error_kind(
    exc: &Bound<'_, PyBaseException>,
    kind: &louis::CompileErrorKind,
) -> PyResult<()> {
    use louis::CompileErrorKind::*;
    let py = exc.py();
    for attribute in ["character", "base", "derived", "swap_class"] {
        exc.setattr(attribute, py.None())?;
    }
    let member = match kind {
        ImplicitCharacterNotDefined(character) => {
            exc.setattr("character", *character)?;
            "IMPLICIT_CHARACTER_NOT_DEFINED"
        }
        BaseCharacterNotDefined { base, derived } => {
            exc.setattr("base", *base)?;
            exc.setattr("derived", *derived)?;
            "BASE_CHARACTER_NOT_DEFINED"
        }
        SwapClassNotDefined(swap_class) => {
            exc.setattr("swap_class", swap_class)?;
            "SWAP_CLASS_NOT_DEFINED"
        }
        _ => return Err(unmapped(kind)),
    };
    exc.setattr("kind", kind_member(py, "CompileErrorKind", member)?)
}

/// The member `member` of the package's enum `kind`.
fn kind_member<'py>(py: Python<'py>, kind: &str, member: &str) -> PyResult<Bound<'py, PyAny>> {
    package(py)?.getattr(kind)?.getattr(member)
}

/// `NotImplementedError` for a louis-rs `error` that louis-py has no kind for.
fn unmapped(error: impl std::fmt::Display) -> PyErr {
    PyNotImplementedError::new_err(format!(
        "louis-py has no kind for this louis-rs error: {error}"
    ))
}

/// The package this module was loaded from.
static PACKAGE: OnceLock<String> = OnceLock::new();

/// The name of the package this module was loaded from.
fn package_name() -> &'static str {
    PACKAGE.get().expect("set when the module is initialized")
}

/// The package this module was loaded from, imported.
fn package(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    py.import(package_name())
}

/// Wrap a `louis::metadata::MetadataError` into the matching
/// `louis_py.metadata` exception.
fn to_metadata_pyerr(err: louis::metadata::MetadataError) -> PyErr {
    Python::attach(|py| metadata_exception(py, &err).unwrap_or_else(|failure| failure))
}

/// `err` as the matching `louis_py.metadata` exception.
fn metadata_exception(py: Python<'_>, err: &louis::metadata::MetadataError) -> PyResult<PyErr> {
    use louis::metadata::MetadataError::*;
    let class = match err {
        InvalidQuery(_) => "InvalidQueryError",
        Io(_) => "MetadataIOError",
        _ => "MetadataError",
    };
    let value = py
        .import(format!("{}.metadata", package_name()))?
        .getattr(class)?
        .call1((err.to_string(),))?;
    if let InvalidQuery(pair) = err {
        value.setattr(intern!(py, "pair"), pair)?;
    }
    Ok(PyErr::from_value(value))
}

/// Check that `obj` is a member of the enum `class` of the package this module was
/// loaded from, raising `TypeError` otherwise.
fn check_enum(obj: &Bound<'_, PyAny>, class: &str) -> PyResult<()> {
    let expected = package(obj.py())?.getattr(class)?;
    if obj.is_instance(&expected)? {
        Ok(())
    } else {
        Err(PyTypeError::new_err(format!(
            "expected {}.{class}, not {}",
            package_name(),
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

/// The result of a translation. Mirrors `louis::TranslationResult`.
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

/// `search_path`, or the directories in `LOUIS_TABLE_PATH` when it is `None`.
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

/// `pairs`, a mapping of keys to values or an iterable of `(key, value)`
/// tuples, as a `louis::metadata::Query`.
fn query_from_pairs(pairs: &Bound<'_, PyAny>) -> PyResult<louis::metadata::Query> {
    let pairs = match pairs.cast::<PyMapping>() {
        Ok(mapping) => mapping.items()?.into_any(),
        Err(_) => pairs.clone(),
    };
    pairs
        .try_iter()?
        .map(|pair| pair?.extract::<(String, String)>())
        .collect()
}

/// A query into the metadata of tables: `key:value` pairs that a table must
/// all carry to match.
#[pyclass(frozen, eq, module = "louis_py.metadata")]
#[derive(PartialEq)]
pub struct Query {
    inner: louis::metadata::Query,
}

#[pymethods]
impl Query {
    /// Build a query from a mapping of keys to values or from `(key, value)`
    /// pairs.
    #[new]
    fn new(pairs: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self {
            inner: query_from_pairs(pairs)?,
        })
    }

    /// Parse a query: `key:value` pairs separated by whitespace, such as
    /// `language:de grade:2`.
    #[staticmethod]
    fn parse(text: &str) -> PyResult<Self> {
        let inner = text.parse().map_err(to_metadata_pyerr)?;
        Ok(Self { inner })
    }

    fn __str__(&self) -> String {
        self.inner.to_string()
    }
}

/// A query given as a `Query`, a string to parse, a mapping of keys to values
/// or `(key, value)` pairs.
#[derive(FromPyObject)]
enum AnyQuery<'py> {
    Query(Bound<'py, Query>),
    Text(String),
    Pairs(Bound<'py, PyAny>),
}

impl AnyQuery<'_> {
    fn into_query(self) -> PyResult<louis::metadata::Query> {
        match self {
            Self::Query(query) => Ok(query.get().inner.clone()),
            Self::Text(text) => text.parse().map_err(to_metadata_pyerr),
            Self::Pairs(pairs) => query_from_pairs(&pairs),
        }
    }
}

/// The `#+key: value` metadata pairs of the tables on a search path, mapped
/// to the tables that carry them.
#[pyclass(frozen, module = "louis_py.metadata")]
pub struct Index {
    inner: louis::metadata::Index,
}

#[pymethods]
impl Index {
    /// Index the tables in `search_path` when given, otherwise in
    /// `LOUIS_TABLE_PATH`, as `Translator` does.
    #[new]
    #[pyo3(signature = (*, search_path = None))]
    fn new(py: Python<'_>, search_path: Option<Vec<PathBuf>>) -> PyResult<Self> {
        let search_path = search_path_or_table_path(search_path);
        let inner = py
            .detach(|| louis::metadata::Index::with_search_path(search_path))
            .map_err(to_metadata_pyerr)?;
        Ok(Self { inner })
    }

    /// The tables that carry every pair of `query`, sorted by path.
    fn find(&self, query: AnyQuery<'_>) -> PyResult<Vec<&Path>> {
        Ok(self.inner.find(&query.into_query()?))
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
    m.add("LOUIS_RS_VERSION", louis::VERSION)?;
    let types = [
        py.get_type::<BrailleEncoding>(),
        py.get_type::<Translator>(),
        py.get_type::<TranslationResult>(),
        py.get_type::<LouisError>(),
        py.get_type::<TableParseError>(),
        py.get_type::<TableCompileError>(),
    ];
    for class in types {
        class.setattr(intern!(py, "__module__"), package)?;
        m.add(class.name()?, class)?;
    }
    let metadata = format!("{package}.metadata");
    for class in [py.get_type::<Index>(), py.get_type::<Query>()] {
        class.setattr(intern!(py, "__module__"), &metadata)?;
        m.add(class.name()?, class)?;
    }
    Ok(())
}
