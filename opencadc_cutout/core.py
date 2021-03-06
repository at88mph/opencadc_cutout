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

import logging
import signal
import sys
import os

from opencadc_cutout.file_helper import FileHelperFactory
from opencadc_cutout.pixel_range_input_parser import PixelRangeInputParser

__all__ = ['OpenCADCCutout']

class OpenCADCCutout(object):
    """
    Main cutout class.  This is mainly used as a parent class for concrete instances, like from a FITS file, but
    can be called by itself if need be.

    Parameters
    ----------
    helper_factory : `.file_helper.FileHelperFactory`
        The Helper Factory instance to load a file helper appropriate to the file type.  Defaults to
        file_helper.FileHelperFactory().

    input_range_parser : `.pixel_range_input_parser.PixelRangeInputParser`
        Parser to parse the input string.  This defaults to the provided
        pixel_range_input_parser.PixelRangeInputParser() class.

    Example 1
    --------
    from opencadc_cutout import OpenCADCCutout

    cutout = OpenCADCCutout()
    output_file = tempfile.mkstemp(suffix='.fits')
    input_file = '/path/to/file.fits'

    # Cutouts are in cfitsio format.
    cutout_region_string = '[300:800,810:1000]'  # HDU 0 along two axes.

    # Needs to have 'append' flag set.  The cutout() method will write out the data.
    with open(output_file, 'ab+') as output_writer, open(input_file, 'rb') as input_reader:
        test_subject.cutout(input_reader, output_writer, cutout_region_string, 'FITS')
        output_writer.close()
        input_reader.close()


    Example 2 (CADC)
    --------
    from opencadc_cutout import OpenCADCCutout
    from cadcdata import CadcDataClient

    cutout = OpenCADCCutout()
    anonSubject = net.Subject()
    data_client = CadcDataClient(anonSubject)
    output_file = tempfile.mkstemp(suffix='.fits')
    archive = 'HST'
    file_name = 'n8i311hiq_raw.fits'
    input_stream = data_client.get_file(archive, file_name)

    # Cutouts are in cfitsio format.
    cutout_region_string = '[SCI,10][80:220,100:150]'  # SCI version 10, along two axes.

    # Needs to have 'append' flag set.  The cutout() method will write out the data.
    with open(output_file, 'ab+') as output_writer:
        test_subject.cutout(input_stream, output_writer, cutout_region_string, 'FITS')
        output_writer.close()
        input_stream.close()
    """

    def __init__(self, helper_factory=FileHelperFactory(), input_range_parser=PixelRangeInputParser()):
        logging.getLogger().setLevel('INFO')
        self.logger = logging.getLogger(__name__)
        self.helper_factory = helper_factory
        self.input_range_parser = input_range_parser

    def cutout(self, input_reader, output_writer, cutout_dimensions_str, file_type):
        """
        Perform a Cutout of the given data at the given position and size.

        Parameters
        ----------
        input_reader: File-like object, Reader stream
            The file location.  The file extension is important as it's used to determine how to process it.

        output_writer: File-like object, Writer stream
            The writer to push the cutout array to.

        cutout_dimensions_str: string of WCS coordinates, or extension and pixel coordinates.
            The requested dimensions expressed as PixelCutoutHDU objects.

        file_type: string
            The file type, in upper case.  Will usually be 'FITS'.
        """
        file_helper = self._get_file_helper(
            file_type, input_reader, output_writer)
        file_helper.cutout(cutout_dimensions_str)

    def _get_file_helper(self, file_type, input_reader, output_writer):
        return self.helper_factory.get_instance(file_type, input_reader, output_writer, self.input_range_parser)
