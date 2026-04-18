---
applyTo: "**/*.qml,**/*.ui.qml,**/app.py,**/ui/**/*.py"
---

# Modern PySide6 + QML instructions

Use these rules when creating or modifying QML in a Python + Qt Quick project.

## Architecture

- Treat QML as the declarative view layer only. Keep business logic, I/O, and long-lived state in Python.
- QML talks to Python through typed `QObject` APIs: `Signal`, `Property`, and `Slot`.
- Prefer QML module-based registration with decorators such as `@QmlElement` and `@QmlSingleton`.
- Prefer typed objects and models over ad-hoc context properties.
- Keep prototype or design-time dummy data in a dedicated `dummydata/` module, one QML type per file.

## QML structure

- Add a `qmldir` file for every reusable or imported QML directory.
- Keep shared design tokens in `Style.qml` as a `pragma Singleton`; use `Style.xxx` directly and never instantiate it.
- Prefer built-in Qt Quick Controls and Qt Quick Layouts before building custom controls.
- When creating reusable styled controls, prefer deriving from `QtQuick.Templates` types and customizing their template parts before building a control from scratch.
- Prefer application-wide theming through the active Qt Quick Controls style and `qtquickcontrols2.conf` before hardcoding colors into individual built-in controls.
- If no style is explicitly required, default to the newest available `FluentWinUI3` and set a `FallbackStyle`.
- If a built-in control needs small visual adjustments, local overrides are acceptable; if the same override pattern is repeated across many instances, create a custom style for that control instead of duplicating the override everywhere.
- Keep control-local presentation and interaction logic in QML when styling template-based components; only fall back to a `Rectangle`-from-scratch component when the control has special behavior or structure that templates and built-in controls cannot express cleanly.
- Prefer `ListView`/`Repeater` + delegate patterns for lists and cards.
- Prefer bundled Qt resources (`qrc:/` or `:/`) over raw filesystem paths for QML, icons, and images.
- Store `qtquickcontrols2.conf` in Qt resources and load it from there so the application can switch or initialize styles reliably at runtime.
- Make user-facing strings translatable from the start with `qsTr()`.

## Imports and style configuration

- In Qt 6 projects, prefer unversioned imports such as `import QtQuick` and `import QtQuick.Controls` so QML can use the latest available API by default.
- Add an import version only when a dependency, deployment target, or feature constraint specifically requires it.
- Always set both `Style` and `FallbackStyle` in `qtquickcontrols2.conf`; do not rely on implicit platform defaults.
- When implementing a custom styled control, it is acceptable to inspect the user's local Qt installation under `qml/QtQuick/Controls/...` to follow the built-in style patterns for `QtQuick.Templates` usage.

## Tooling

- When modifying Python classes that are exposed to QML, regenerate the stub metadata with `pyside6-qml-stubgen.exe src --out-dir ./qmltypes`.
- Keep the generated files in the repository root `./qmltypes` directory so QML tooling can resolve the Python-backed types consistently.
- After editing QML files, run `pyside6-qmllint -I ./qmltypes <qml-files>` to catch unresolved types and related QML issues.
- Format modified QML files with `pyside6-qmlformat -i <qml-files>`.
- For editor support, point the QML language server at `./qmltypes` via `qt-qml.qmlls.additionalImportPaths` (for example in `.vscode/settings.json`).

## Input and state

- Prefer Pointer Handlers (`TapHandler`, `HoverHandler`, `DragHandler`, `WheelHandler`) over `MouseArea` for pointer input.
- Use `MouseArea` only when Pointer Handlers cannot express the behavior cleanly.
- Keep state in models or Python controllers, not in delegates. Delegates should render data and emit signals upward.
- Prefer `required property` for delegate inputs instead of reaching through `parent`, `model`, or outer IDs.
- Prefer explicit interaction signals such as `onTapped`, `onMoved`, or `onActivated` over generic `...Changed` handlers for user actions.

## Layout and sizing

- A layout may use anchors against its non-layout parent, but immediate children of `RowLayout`/`ColumnLayout`/`GridLayout` must use `Layout.*`, not anchors.
- Rely on `implicitWidth` and `implicitHeight` where possible; do not fight control sizing with unnecessary fixed values.
- Avoid nesting layouts and anchors when simple `x`, `y`, `width`, or `height` bindings are enough, especially inside delegates.
- If you customize `Menu`, `Popup`, `MenuItem`, `MenuSeparator`, or other control backgrounds/delegates, give them sensible `implicitWidth` and `implicitHeight`.
- For secondary windows on desktop, prefer native window flags for title-bar buttons instead of drawing fake close buttons inside content.
- Prefer scalable assets: SVG for small icons, and multi-resolution image assets when raster images are required.

## Bindings and maintainability

- Prefer declarative bindings over `Component.onCompleted` assignments and other imperative property setup.
- Prefer concrete property types over `var` when the type is known.
- Avoid unqualified access and fragile `parent.xxx` references in custom delegates; give items explicit IDs when needed.
- Avoid nested conditional expressions for visual state styling; prefer explicit `states` + `PropertyChanges` state machines so control states stay easy to inspect and revise.
- Keep inline JavaScript small and view-local. If logic becomes stateful, reusable, or data-oriented, move it to Python.
- If using Qt Design Studio, keep `.ui.qml` files visual-only and move unsupported logic into plain `.qml` files.
- If customizing controls, base them on a non-native customizable style such as `Basic` or `Fusion`, not a native platform style.
- Tap handlers should use `gesturePolicy: TapHandler.WithinBounds` to avoid accidentally triggering taps when the user is trying to scroll or interact with something else nearby.
