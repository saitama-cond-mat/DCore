FILE(COPY dir-intJ DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY dir-intW DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY dir-wan DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY dir-wfn DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY sr2vo4_geom_ref.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY sr2vo4_hr_ref.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY sr2vo4_jr_ref.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY sr2vo4_ur_ref.dat DESTINATION ${CMAKE_CURRENT_BINARY_DIR})
FILE(COPY ../../tools/respack2wan90.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

triqs_add_python_test(respack)
