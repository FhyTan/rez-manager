import QtQuick 2.15
import QtQuick.Controls 2.15
import "DarkRezStyle"

ApplicationWindow {
    id: root

    visible: true
    width: 800
    height: 600

    ComboBox {
        id: combo
        model: ["Option 1", "Option 2", "Option 3"]
        currentIndex: 0
    }
}
