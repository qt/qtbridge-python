
# Headers that contain Q_OBJECT and need MOC processing
# TODO: Basically we don't need MOC for this because we manipulate
# meta objects manually, but for now we keep it and remove it later
# if we are sure everything works fine without it.
set(qtbridge_MOC_HEADERS
    autoqmlbridgemodel_p.h
)

# All other headers
set(qtbridge_HEADERS
    autoqmlbridge_p.h
    pycapsule_p.h
    updateqmldecorators/updateqmldecorator_p.h
    updateqmldecorators/decoratorhelpers.h
    errorhandler.h
    bridgespep384.h
    conversion_p.h
    qmlregistertype_p.h
    helpers_p.h
    qmllistproperty_p.h
)


# Generate MOC files for headers with Q_OBJECT
qt_wrap_cpp(qtbridge_MOC_SOURCES ${qtbridge_MOC_HEADERS})

set(qtbridge_SOURCES
    autoqmlbridge.cpp
    autoqmlbridgemodel.cpp
    pycapsule.cpp
    updateqmldecorators/updateqmldecorator.cpp
    updateqmldecorators/decoratorhelpers.cpp
    updateqmldecorators/insertdecorator.cpp
    updateqmldecorators/removedecorator.cpp
    updateqmldecorators/movedecorator.cpp
    updateqmldecorators/editdecorator.cpp
    updateqmldecorators/resetdecorator.cpp
    updateqmldecorators/completedecorator.cpp
    qtbridges_module.cpp
    errorhandler.cpp
    bridgespep384.cpp
    conversion.cpp
    qmlregistertype.cpp
    helpers.cpp
    qmllistproperty.cpp
    ${qtbridge_MOC_SOURCES}  # Include generated MOC sources
)

if (SKBUILD_SABI_COMPONENT)
    message(STATUS "Building with Stable ABI support")
    python_add_library(qtbridge MODULE WITH_SOABI
        USE_SABI ${SKBUILD_SABI_VERSION}
        ${qtbridge_HEADERS}
        ${qtbridge_MOC_HEADERS}
        ${qtbridge_SOURCES}
    )
else()
    message(STATUS "Building without Stable ABI support")
    python_add_library(qtbridge MODULE
        ${qtbridge_HEADERS}
        ${qtbridge_MOC_HEADERS}
        ${qtbridge_SOURCES}
    )
endif()

# Get the include directories from the imported target
get_target_property(SHIBOKEN_INCLUDE_DIRS Shiboken6::libshiboken INTERFACE_INCLUDE_DIRECTORIES)
get_target_property(PYSIDE_INCLUDE_DIRS PySide6::pyside6 INTERFACE_INCLUDE_DIRECTORIES)

target_include_directories(qtbridge PRIVATE
    ${Python_INCLUDE_DIRS}
    ${SHIBOKEN_INCLUDE_DIR}
    ${PYSIDE_INCLUDE_DIR}
    ${Qt6Core_INCLUDE_DIRS}
    ${Qt6Qml_INCLUDE_DIRS}
)

target_link_libraries(qtbridge PRIVATE
    Qt6::Core
    Qt6::CorePrivate
    Qt6::Qml
    Qt6::QmlPrivate
    Shiboken6::libshiboken
    PySide6::pyside6
)

set_target_properties(qtbridge
    PROPERTIES
        PREFIX ""
        SUFFIX "${Python_EXTENSION_SUFFIX}"
        OUTPUT_NAME "QtBridge"
)

if(WIN32)
    set(MODULE_SUFFIX ".pyd")
else()
    set(MODULE_SUFFIX ".abi3.so")
endif()

set_target_properties(qtbridge
    PROPERTIES
        PREFIX ""
        SUFFIX "${MODULE_SUFFIX}"
        OUTPUT_NAME "QtBridge"
)

if(WIN32)
    # Copy required Qt DLLs to output directory during installation
    install(CODE "
        file(GET_RUNTIME_DEPENDENCIES
            RESOLVED_DEPENDENCIES_VAR DEPS
            UNRESOLVED_DEPENDENCIES_VAR UNRESOLVED_DEPS
            DIRECTORIES
                \${Python_SITELIB}/PySide6
                \${Python_SITELIB}/shiboken6
            EXECUTABLES \$<TARGET_FILE:qtbridge>
        )

        # Install resolved dependencies alongside the module
        foreach(dep IN LISTS DEPS)
            file(INSTALL
                DESTINATION ${SKBUILD_PROJECT_NAME}
                TYPE SHARED_LIBRARY
                FILES \${dep}
            )
        endforeach()
    ")
else()
    # Linux/macOS: Set RPATH to find Qt libraries from PySide6
    if(APPLE)
        set(RPATH_TOKEN "@loader_path")
    else()
        set(RPATH_TOKEN "$ORIGIN")
    endif()

    set_target_properties(qtbridge PROPERTIES
        BUILD_WITH_INSTALL_RPATH TRUE
        INSTALL_RPATH "${RPATH_TOKEN}/../PySide6/Qt/lib;${RPATH_TOKEN}/../PySide6;${RPATH_TOKEN}/../shiboken6"
    )
endif()

install(TARGETS qtbridge DESTINATION ${SKBUILD_PROJECT_NAME})
