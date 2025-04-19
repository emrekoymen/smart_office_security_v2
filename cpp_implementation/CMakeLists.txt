cmake_minimum_required(VERSION 3.5)
project(smart_office_security_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(OPENCV4 REQUIRED opencv4)

find_package(Boost REQUIRED COMPONENTS system)
find_package(Threads REQUIRED)

# Locate TensorFlow Lite C library (libtensorflowlite_c.so) instead of C++ lib
find_library(TFLITE_C_LIB tensorflowlite_c HINTS /usr/local/lib)
if(NOT TFLITE_C_LIB)
  message(FATAL_ERROR "Could not find TensorFlow Lite C library (libtensorflowlite_c.so). Please install/download the TFLite C API and copy libtensorflowlite_c.so to /usr/local/lib.")
endif()

include_directories(
  ${OPENCV4_INCLUDE_DIRS}
  ${Boost_INCLUDE_DIRS}
  /usr/local/include
  /usr/include
)

link_directories(
  /usr/local/lib
  /usr/lib/x86_64-linux-gnu
  ${OPENCV4_LIBRARY_DIRS}
)

add_executable(smart_office_security
  src/main.cpp
  src/CameraStream.cpp
  src/DisplayWindow.cpp
  src/PersonDetector.cpp
  src/ZigbeeSender.cpp
)

target_link_libraries(smart_office_security
  ${OPENCV4_LIBRARIES}
  ${Boost_LIBRARIES}
  ${TFLITE_C_LIB}
  edgetpu
  Threads::Threads
)
