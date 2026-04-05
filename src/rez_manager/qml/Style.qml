pragma Singleton
import QtQuick 2.15

// Singleton style sheet — access as Style.accent, Style.fontMd etc. from any QML file.
// Import the parent module (import "..") to activate this singleton in sub-directories.
QtObject {
    // ── Backgrounds ──────────────────────────────────────────
    readonly property color bg:         "#0E0E16"
    readonly property color surface:    "#13131E"
    readonly property color elevated:   "#1A1A28"
    readonly property color card:       "#1C1C2C"
    readonly property color cardHover:  "#222234"
    readonly property color sidebar:    "#101018"

    // ── Text ─────────────────────────────────────────────────
    readonly property color textPrimary:   "#E8EAFA"
    readonly property color textSecondary: "#9090B8"
    readonly property color textDisabled:  "#4E4E72"
    readonly property color white:         "#FFFFFF"

    // ── Accent ───────────────────────────────────────────────
    readonly property color accent:          "#5F83FF"
    readonly property color accentHover:     "#7094FF"
    readonly property color accentDim:       "#1A2550"
    readonly property color accentSecondary: "#8A58D8"   // purple gradient partner

    // ── Borders ──────────────────────────────────────────────
    readonly property color border:       "#1E1E32"
    readonly property color borderBright: "#2A2A44"

    // ── Semantic ─────────────────────────────────────────────
    readonly property color success: "#4DB880"
    readonly property color warning: "#D98A38"
    readonly property color error:   "#D94F68"
    readonly property color info:    "#4A88D8"

    // ── Launch target palette ─────────────────────────────────
    readonly property color colorMaya:    "#4DB880"
    readonly property color colorHoudini: "#D98A38"
    readonly property color colorShell:   "#4A88D8"
    readonly property color colorCustom:  "#8A58D8"

    // ── Shape ────────────────────────────────────────────────
    readonly property int radius:   8
    readonly property int radiusSm: 4
    readonly property int radiusLg: 12

    // ── Spacing ──────────────────────────────────────────────
    readonly property int xs:  4
    readonly property int sm:  8
    readonly property int md:  12
    readonly property int lg:  16
    readonly property int xl:  24
    readonly property int xxl: 32

    // ── Font sizes ───────────────────────────────────────────
    readonly property int fontXs:  10
    readonly property int fontSm:  12
    readonly property int fontMd:  13
    readonly property int fontLg:  15
    readonly property int fontXl:  18
    readonly property int fontXxl: 22

    // ── Helpers ──────────────────────────────────────────────
    function launchColor(target) {
        if (target === "maya")    return colorMaya
        if (target === "houdini") return colorHoudini
        if (target === "shell")   return colorShell
        if (target === "custom")  return colorCustom
        return textSecondary
    }

    function launchLabel(target) {
        if (target === "maya")    return "Maya"
        if (target === "houdini") return "Houdini"
        if (target === "shell")   return "Shell"
        if (target === "custom")  return "Custom"
        return target
    }
}
