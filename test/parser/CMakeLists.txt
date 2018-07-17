FILE(COPY parser.in DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

add_test(NAME parser COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/parser.py)

# Set the PythonPath : put the build dir first (in case there is an installed version). 
set_property(TEST parser PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/python:$ENV{PYTHONPATH} )
