FILE(COPY  stan_ref_bethe.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY  stan_ref_chain.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY  stan_ref_cubic.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY stan_ref_square.h5 DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

add_test(NAME pre_preset COMMAND python ${CMAKE_CURRENT_SOURCE_DIR}/pre_preset.py)
# Set the PythonPath : put the build dir first (in case there is an installed version).
set_property(TEST pre_preset PROPERTY ENVIRONMENT PYTHONPATH=${CMAKE_BINARY_DIR}/python:$ENV{PYTHONPATH} )

