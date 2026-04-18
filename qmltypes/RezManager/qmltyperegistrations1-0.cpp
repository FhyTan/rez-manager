/****************************************************************************
** Generated QML type registration code
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <QtQml/qqml.h>
#include <QtQml/qqmlmoduleregistration.h>

#if __has_include(<D:/Code/rez-manager/src/rez_manager/ui/main_window.py>)
#  include <D:/Code/rez-manager/src/rez_manager/ui/main_window.py>
#endif
#if __has_include(<D:/Code/rez-manager/src/rez_manager/ui/package_manager.py>)
#  include <D:/Code/rez-manager/src/rez_manager/ui/package_manager.py>
#endif
#if __has_include(<D:/Code/rez-manager/src/rez_manager/ui/settings_controller.py>)
#  include <D:/Code/rez-manager/src/rez_manager/ui/settings_controller.py>
#endif


#if !defined(QT_STATIC)
#define Q_QMLTYPE_EXPORT Q_DECL_EXPORT
#else
#define Q_QMLTYPE_EXPORT
#endif
Q_QMLTYPE_EXPORT void qml_register_types_RezManager()
{
    QT_WARNING_PUSH QT_WARNING_DISABLE_DEPRECATED
    qmlRegisterTypesAndRevisions<AppSettingsController>("RezManager", 1);
    qmlRegisterTypesAndRevisions<PackageManagerController>("RezManager", 1);
    qmlRegisterTypesAndRevisions<ProjectListModel>("RezManager", 1);
    qmlRegisterAnonymousType<QAbstractItemModel, 254>("RezManager", 1);
    qmlRegisterTypesAndRevisions<RezContextListModel>("RezManager", 1);
    QT_WARNING_POP
    qmlRegisterModule("RezManager", 1, 0);
}

static const QQmlModuleRegistration rezManagerRegistration("RezManager", qml_register_types_RezManager);
