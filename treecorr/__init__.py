# Copyright (c) 2003-2014 by Mike Jarvis
#
# TreeCorr is free software: redistribution and use in source and binary forms,
# with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions, and the disclaimer given in the accompanying LICENSE
#    file.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions, and the disclaimer given in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the {organization} nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.


version = '3.0beta'

from .config import read_config
from .celestial import CelestialCoord, angle_units
from .corr2 import corr2, print_corr2_params
from .catalog import Catalog, read_catalogs, calculateVarG, calculateVarK
from .binnedcorr2 import BinnedCorr2, SetOMPThreads
from .g2correlation import G2Correlation
from .n2correlation import N2Correlation
from .k2correlation import K2Correlation
from .ngcorrelation import NGCorrelation
from .nkcorrelation import NKCorrelation
from .kgcorrelation import KGCorrelation
from .field import NField, KField, GField, NSimpleField, KSimpleField, GSimpleField
