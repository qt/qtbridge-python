# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: BSD-3-Clause

cmake_minimum_required(VERSION 3.27)

# for clang-tidy
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Always generate compile_commands.json for IDE integration
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

project(${SKBUILD_PROJECT_NAME})

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "Configuring for Debug build")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g3 -O0")
    set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g3 -O0")
    add_definitions(-DDEBUG_BUILD)
endif()

find_package(Python COMPONENTS Interpreter Development.SABIModule REQUIRED)
message(STATUS "Using Stable ABI with version ${SKBUILD_SABI_VERSION}")

# Add Python site-packages directories to CMAKE_PREFIX_PATH to find PySide6/shiboken6
# On some distros (RHEL,), binary wheels install to lib64/ instead of lib/
execute_process(
    COMMAND ${Python_EXECUTABLE} -c "import site; print(';'.join(site.getsitepackages()))"
    OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(PYTHON_SITE_PACKAGES)
    message(STATUS "Adding Python site-packages to CMAKE_PREFIX_PATH: ${PYTHON_SITE_PACKAGES}")
    list(APPEND CMAKE_PREFIX_PATH ${PYTHON_SITE_PACKAGES})
endif()

# check for qtpaths
if(NOT DEFINED QT_PATHS)
    find_program(QT_PATHS qtpaths)
    if(NOT QT_PATHS)
        message(FATAL_ERROR
            "qtpaths not found. Please set QT_PATHS by passing "
            "-Ccmake.define.QT_PATHS=/path/to/qtpaths to pip/build, or ensure qtpaths is in the PATH."
        )
    endif()
endif()

# Use qtpaths to determine the Qt6 installation prefix
execute_process(
    COMMAND ${QT_PATHS} --install-prefix
    OUTPUT_VARIABLE QT_INSTALL_PREFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT QT_INSTALL_PREFIX)
    message(FATAL_ERROR "Failed to determine Qt installation prefix using qtpaths.")
endif()

# Add the relevant installation prefix to CMAKE_PREFIX_PATH
list(APPEND CMAKE_PREFIX_PATH "${QT_INSTALL_PREFIX}/lib/cmake")

# Find Qt6
find_package(Qt6 REQUIRED COMPONENTS Core Qml CorePrivate QmlPrivate)
find_package(Shiboken6 CONFIG REQUIRED)
find_package(PySide6 CONFIG REQUIRED)

# Add the subdirectory containing the extension module
add_subdirectory(src/QtBridge)
