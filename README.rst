GeoServer Explorer QGIS Plugin
*******************************

A plugin to configure and manage GeoServer from QGIS.

Installation
=============

To install, run the following in a terminal (you will need to have `paver <http://paver.github.io/paver/>`_ installed):

::

	$ paver setup
	$ paver install

The first command will fetch the dependencies required by the plugin. The second one will install the plugin in your local QGIS plugins folder. Open QGIS and you should already see the GeoServer Explorer plugin available in your QGIS plugin manager.

Getting Help
============

Usage is documented `here <http://boundlessgeo.github.io/qgis-geoserver-plugin>`_

If you have questions, please use the project `mailing list <https://groups.google.com/forum/#!forum/qgis-geoserver-plugin>`_

Use the Github project for any bug reports. Pull requests are welcome.



Cloning this repository
=======================

This repository uses external repositories as submodules. Therefore in order to include the external repositories during cloning you should use the *--recursive* option:

git clone --recursive http://github.com/boundlessgeo/qgis-geoserver-plugin.git

Also, to update the submodules whenever there are changes in the remote repositories one should do:

git submodule update --remote
