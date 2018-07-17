FILE(COPY  dmft.ini DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY  test.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY  test_ref.out.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

add_test(NAME main_chain_triqsqmc COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/main_chain_triqsqmc.py)
# Set the PythonPath : put the build dir first (in case there is an installed version).
set_property(TEST main_chain_triqsqmc PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/python:$ENV{PYTHONPATH} )

