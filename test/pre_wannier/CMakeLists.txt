FILE(COPY nis_hr.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY nis_ref.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

add_test(NAME pre_wannier COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/pre_wannier.py)
# Set the PythonPath : put the build dir first (in case there is an installed version).
set_property(TEST pre_wannier PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/python:$ENV{PYTHONPATH} )

