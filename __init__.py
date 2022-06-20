# -*- coding: utf-8 -*-


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load DMIOpenData class from file DMIOpenData.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .DMI_Open_Data import DMIOpenData
    return DMIOpenData(iface)
