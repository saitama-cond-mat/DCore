FILE(COPY test_hr.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY test_jr.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY test_ur.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY test_ref.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY dmft.ini DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

add_test(NAME pre_respack_so COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/pre_respack_so.py)
# Set the PythonPath : put the build dir first (in case there is an installed version).
set_property(TEST pre_respack_so PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/python:$ENV{PYTHONPATH} )

