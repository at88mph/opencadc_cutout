# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2018.                            (c) 2018.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU AfferoF
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 1 $
#
# ***********************************************************************
#

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import numpy as np

from copy import deepcopy

from astropy.nddata.utils import extract_array, Cutout2D
from .range_parser import RangeParser


class CutoutResult(object):
    """
    Just a DTO to move results of a cutout.  It's more readable than a plain tuple.
    """

    def __init__(self, data, wcs=None):
        self.data = data
        self.wcs = wcs


class CutoutND(object):
    """
      Parameters
      ----------
      data : `~numpy.ndarray`
          The N-dimensional data array from which to extract the cutout array.
      cutout_region : `PixelCutoutHDU`
          The Pixel HDU Cutout description.  See opencadc_cutout.pixel_cutout_hdu.py.
      wcs : `~astropy.wcs.WCS` or `None`
          A WCS object associated with the cutout array.  If it's specified, reset the WCS values for the cutout.

      Returns
      -------
      CutoutResult instance
    """

    def __init__(self, data, range_parser=RangeParser(), wcs=None):
        self.logger = logging.getLogger()
        self.logger.setLevel('DEBUG')
        self.data = data
        self.wcs = wcs
        self.range_parser = range_parser

    def _get_position_shape(self, data_shape, cutout_region):
        requested_shape = cutout_region.get_shape()
        requested_position = cutout_region.get_position()

        # reverse position because extract_array uses reverse ordering (i.e. x,y -> y,x).
        r_position = tuple(reversed(requested_position))
        r_shape = tuple(reversed(requested_shape))

        len_data = len(data_shape)
        len_pos = len(r_position)
        len_shape = len(r_shape)

        if len_shape > len_data:
            raise ValueError('Invalid shape requested (tried to extract {} from {}).'.format(
                r_shape, data_shape))

        shape = (data_shape[:(len_data - len_shape)]) + r_shape

        if len_pos > len_data:
            raise ValueError('Invalid position requested (tried to extract {} from {}).'.format(
                r_position, data_shape))

        position = (data_shape[:(len_data - len_pos)]) + r_position

        return (tuple(position), tuple(shape))

    def extract(self, cutout_region):
        data = np.asanyarray(self.data)
        data_shape = data.shape
        position, shape = self._get_position_shape(data_shape, cutout_region)
        cutout_data = extract_array(data, shape, position, mode='trim')

        if self.wcs is not None:
            output_wcs = deepcopy(self.wcs)
            wcs_crpix = output_wcs.wcs.crpix

            for idx, r in enumerate(cutout_region.get_ranges()):
                wcs_crpix[idx] -= (r[0] - 1)

            output_wcs._naxis = list(cutout_data.shape)
            # if output_wcs.sip is not None:
            #     output_wcs.sip = Sip(output_wcs.sip.a, output_wcs.sip.b, output_wcs.sip.ap,
            #                          output_wcs.sip.bp, output_wcs.sip.crpix - self._origin_original_true)
        else:
            output_wcs = None

        return CutoutResult(data=cutout_data, wcs=output_wcs)