import "components"

PackageDetailPanel {
    selectedPkgName: "test_pkg"
    pkgDetail: {
        "name": "test_pkg",
        "versions": ["1.0.0", "1.1.0", "2.0.0"],
        "description": "This is a test package.long long long long long description text to test the UI layout and text wrapping capabilities of the detail panel.",
        "requires": [""],
        "variants": ["long long long long long variant1", "variant2"],
        "tools": ["long long long long long tool1", "tool2"],
        "code": "def build():\n    print('Building test_pkg')"
    }
}
