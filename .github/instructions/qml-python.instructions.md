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
- Prefer built-in Qt Quick Controls and Qt Quick Layouts before building custom controls from `Rectangle + Text`.
- Prefer `ListView`/`Repeater` + delegate patterns for lists and cards.
- Prefer bundled Qt resources (`qrc:/` or `:/`) over raw filesystem paths for QML, icons, and images.
- Make user-facing strings translatable from the start with `qsTr()`.

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
- Keep inline JavaScript small and view-local. If logic becomes stateful, reusable, or data-oriented, move it to Python.
- If using Qt Design Studio, keep `.ui.qml` files visual-only and move unsupported logic into plain `.qml` files.
- If customizing controls, base them on a non-native customizable style such as `Basic` or `Fusion`, not a native platform style.
- Keep QML comments rare and only for non-obvious behavior.
