#
# DCore -- Integrated DMFT software for correlated electrons
# Copyright (C) 2017 The University of Tokyo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import print_function
from numdiff import numdiff
from respack2wan90 import respack2wan90
#
respack2wan90("sr2vo4")

numdiff("sr2vo4_hr.dat", "sr2vo4_hr_ref.dat")
numdiff("sr2vo4_ur.dat", "sr2vo4_ur_ref.dat")
numdiff("sr2vo4_jr.dat", "sr2vo4_jr_ref.dat")
numdiff("sr2vo4_geom.dat", "sr2vo4_geom_ref.dat")
