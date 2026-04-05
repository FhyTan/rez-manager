// ProjectListModel.qml — dummy implementation of the Python ProjectListModel.
//
// Python equivalent (to be implemented in src/rez_manager/ui/):
//   class ProjectListModel(QAbstractListModel):
//       Roles: name (str), avatarColor (str)
//
// Replace by registering the Python class as QML type "ProjectListModel"
// and removing the dummydata import in main.qml.

import QtQuick 2.15

ListModel {
    ListElement { name: "VFX Pipeline"; avatarColor: "#5F83FF" }
    ListElement { name: "Maya Rigging"; avatarColor: "#4DB880" }
    ListElement { name: "Houdini FX";   avatarColor: "#D98A38" }
    ListElement { name: "USD Pipeline"; avatarColor: "#8A58D8" }
}
