"""
mfchd module.  Contains the ModflowChd class. Note that the user can access
the ModflowChd class as `flopy.modflow.ModflowChd`.

Additional information for this MODFLOW package can be found at the `Online
MODFLOW Guide
<http://water.usgs.gov/ogw/modflow-nwt/MODFLOW-NWT-Guide/chd.htm>`_.

"""

import sys
import numpy as np
from ..pakbase import Package
from flopy.utils.util_list import MfList


class ModflowChd(Package):
    """
    MODFLOW Constant Head Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.Modflow`) to which
        this package will be added.
    stress_period_data : list of boundaries, recarrays, or dictionary of
        boundaries.

        Each chd cell is defined through definition of
        layer (int), row (int), column (int), shead (float), ehead (float)
        shead is the head at the start of the stress period, and ehead is the
        head at the end of the stress period.
        The simplest form is a dictionary with a lists of boundaries for each
        stress period, where each list of boundaries itself is a list of
        boundaries. Indices of the dictionary are the numbers of the stress
        period. This gives the form of::

            stress_period_data =
            {0: [
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead]
                ],
            1:  [
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead]
                ], ...
            kper:
                [
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead],
                [lay, row, col, shead, ehead]
                ]
            }

        Note that if the number of lists is smaller than the number of stress
        periods, then the last list of chds will apply until the end of the
        simulation. Full details of all options to specify stress_period_data
        can be found in the flopy3 boundaries Notebook in the basic
        subdirectory of the examples directory.

    extension : string
        Filename extension (default is 'chd')
    unitnumber : int
        File unit number (default is 24).

    Attributes
    ----------
    mxactc : int
        Maximum number of chds for all stress periods.  This is calculated
        automatically by FloPy based on the information in
        stress_period_data.

    Methods
    -------

    See Also
    --------

    Notes
    -----
    Parameters are supported in Flopy only when reading in existing models.
    Parameter values are converted to native values in Flopy and the
    connection to "parameters" is thus nonexistent.

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modflow.Modflow()
    >>> lrcd = {0:[[2, 3, 4, 10., 10.1]]}   #this chd will be applied to all
    >>>                                     #stress periods
    >>> chd = flopy.modflow.ModflowChd(m, stress_period_data=lrcd)

    """

    def __init__(self, model, stress_period_data=None, dtype=None,
                 options=None, extension='chd', unitnumber=None,
                 filenames=None, **kwargs):

        # set default unit number if one is not specified
        if unitnumber is None:
            unitnumber = ModflowChd.defaultunit()

        # set filenames
        if filenames is None:
            filenames = [None, None]
        elif isinstance(filenames, str):
            filenames = [filenames, None]
        elif isinstance(filenames, list):
            if len(filenames) < 2:
                filenames.append(None)

        # Fill namefile items
        name = [ModflowChd.ftype()]
        units = [unitnumber]
        extra = ['']

        # set package name
        fname = [filenames[0]]

        # Call ancestor's init to set self.parent, extension, name and unit number
        Package.__init__(self, model, extension=extension, name=name,
                         unit_number=units, extra=extra, filenames=fname)


        self.url = 'chd.htm'
        self.heading = '# {} package for '.format(self.name[0]) + \
                       ' {}, '.format(model.version_types[model.version]) + \
                       'generated by Flopy.'

        if dtype is not None:
            self.dtype = dtype
        else:
            self.dtype = self.get_default_dtype(structured=self.parent.structured)
        self.stress_period_data = MfList(self, stress_period_data)

        self.np = 0
        if options is None:
            options = []
        self.options = options
        self.parent.add_package(self)

    def ncells(self):
        # Returns the  maximum number of cells that have recharge (developed for MT3DMS SSM package)
        return self.stress_period_data.mxact

    def write_file(self):
        """
        Write the package file.

        Returns
        -------
        None

        """
        f_chd = open(self.fn_path, 'w')
        f_chd.write('{0:s}\n'.format(self.heading))
        f_chd.write(' {0:9d}'.format(self.stress_period_data.mxact))
        for option in self.options:
            f_chd.write('  {}'.format(option))
        f_chd.write('\n')
        self.stress_period_data.write_transient(f_chd)
        f_chd.close()

    def add_record(self, kper, index, values):
        try:
            self.stress_period_data.add_record(kper, index, values)
        except Exception as e:
            raise Exception("mfchd error adding record to list: " + str(e))


    @staticmethod
    def get_empty(ncells=0, aux_names=None, structured=True):
        # get an empty recaray that corresponds to dtype
        dtype = ModflowChd.get_default_dtype(structured=structured)
        if aux_names is not None:
            dtype = Package.add_to_dtype(dtype, aux_names, np.float32)
        d = np.zeros((ncells, len(dtype)), dtype=dtype)
        d[:, :] = -1.0E+10
        return np.core.records.fromarrays(d.transpose(), dtype=dtype)

    @staticmethod
    def get_default_dtype(structured=True):
        if structured:
            dtype = np.dtype([("k", np.int), ("i", np.int),
                              ("j", np.int), ("shead", np.float32),
                              ("ehead", np.float32)])
        else:
            dtype = np.dtype([("node", np.int), ("shead", np.float32),
                              ("ehead", np.float32)])
        return dtype

    @staticmethod
    def load(f, model, nper=None, ext_unit_dict=None):
        """
        Load an existing package.

        Parameters
        ----------
        f : filename or file handle
            File to load.
        model : model object
            The model object (of type :class:`flopy.modflow.mf.Modflow`) to
            which this package will be added.
        nper : int
            The number of stress periods.  If nper is None, then nper will be
            obtained from the model object. (default is None).
        ext_unit_dict : dictionary, optional
            If the arrays in the file are specified using EXTERNAL,
            or older style array control records, then `f` should be a file
            handle.  In this case ext_unit_dict is required, which can be
            constructed using the function
            :class:`flopy.utils.mfreadnam.parsenamefile`.

        Returns
        -------
        chd : ModflowChd object
            ModflowChd object.

        Examples
        --------

        >>> import flopy
        >>> m = flopy.modflow.Modflow()
        >>> wel = flopy.modflow.ModflowChd.load('test.chd', m)

        """

        if model.verbose:
            sys.stdout.write('loading chd package file...\n')

        return Package.load(model, ModflowChd, f, nper,
                            ext_unit_dict=ext_unit_dict)


    @staticmethod
    def ftype():
        return 'CHD'


    @staticmethod
    def defaultunit():
        return 24
