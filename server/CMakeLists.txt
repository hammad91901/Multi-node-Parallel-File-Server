cmake_minimum_required(VERSION 3.10)
project(ParallelFileServer)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenMP
find_package(OpenMP REQUIRED)

# Add executable
add_executable(server main.cpp)

# Link OpenMP
target_link_libraries(server PUBLIC OpenMP::OpenMP_CXX)

# Platform-specific settings
if(WIN32)
    target_link_libraries(server ws2_32)
endif()

# Compiler-specific flags
if(MSVC)
    target_compile_options(server PRIVATE /W4)
else()
    target_compile_options(server PRIVATE -Wall -Wextra -O2)
endif()

