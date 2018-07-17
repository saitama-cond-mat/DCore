# Default to Release build type
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Type of build" FORCE)
endif()
message( STATUS "-------- BUILD-TYPE: ${CMAKE_BUILD_TYPE} -------------")

# start configuration
cmake_minimum_required(VERSION 2.8)
project(DCore CXX Fortran)

# Load TRIQS and Cpp2Py
find_package(TRIQS 2.0 REQUIRED)
find_package(Cpp2Py 1.5 REQUIRED)

if (NOT ${TRIQS_WITH_PYTHON_SUPPORT})
 MESSAGE(FATAL_ERROR "DCore require Python support in TRIQS")
endif()

# Default Install directory to TRIQS_ROOT if not given. Checks an absolute name is given.
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT OR (NOT IS_ABSOLUTE ${CMAKE_INSTALL_PREFIX}))
  message(STATUS " No install prefix given (or invalid). Defaulting to TRIQS_ROOT")
  set(CMAKE_INSTALL_PREFIX ${TRIQS_ROOT} CACHE PATH "default install path" FORCE)
endif()
message(STATUS "-------- CMAKE_INSTALL_PREFIX: ${CMAKE_INSTALL_PREFIX} -------------")

# Use git to detect Cthyb version and git hash
execute_process(COMMAND bash "-c" "${TRIQS_GIT_EXECUTABLE} describe | sed \"s/-\\([0-9]*\\)-.*/.\\1/g\""
 WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
 OUTPUT_VARIABLE   DCORE_VERSION
 OUTPUT_STRIP_TRAILING_WHITESPACE
)
if(NOT DCORE_VERSION)
  set(DCORE_VERSION v2.0.0)
endif()
triqs_get_git_hash_of_source_dir(DCORE_GIT_HASH)
MESSAGE(STATUS "DCore version : ${DCORE_VERSION}")
message(STATUS "Git hash: ${DCORE_GIT_HASH}")

# Add the compiling options (-D... ) for C++
message(STATUS "TRIQS : Adding compilation flags detected by the library (C++11/14, libc++, etc...) ")

add_subdirectory(fortran) 
add_subdirectory(python)
add_subdirectory(shells)
add_subdirectory(tools)

#------------------------
# tests
#------------------------
 
enable_testing()
 
option(Build_Tests "Build the tests of the library " ON)
if (Build_Tests)
  message(STATUS "-------- Preparing tests  -------------")
 add_subdirectory(test)
endif()

#------------------------
# Documentation
#------------------------
option(Build_Documentation "Build documentation" OFF)
if(${Build_Documentation})
  if(NOT ${TRIQS_WITH_DOCUMENTATION})
    message("Error: TRIQS library has not been compiled with its documentation")
  endif()
  add_subdirectory(doc)
endif()
