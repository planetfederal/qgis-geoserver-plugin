#===============================================================================
# import unittest
# from qgis.core import *
# import sys
# import os
# import urllib
#
# keyfile = os.path.join(os.path.dirname(__file__), "resources", "rod.key.pem")
# certfile = os.path.join(os.path.dirname(__file__), "resources", "rod.crt.pem")
# cafile =  os.path.join(os.path.dirname(__file__), "resources", "ca.pem")
#
# class PKITests(unittest.TestCase):
#     '''
#     Tests for PKI support in QGIS
#     Requires a Geoserver catalog with pki auth on localhost:8443 with the default sample data
#     '''
#
#     def testOpenWFSLayer(self):
#         params = {
#             'service': 'WFS',
#             'version': '1.0.0',
#             'request': 'GetFeature',
#             'typename': 'poly_landmarks',
#             'srsname': 'EPSG:4326',
#             'certid': certfile,
#             'keyid': keyfile,
#             'issuerid': cafile
#         }
#         uri = 'http://localhost:8443/geoserver/wfs?' +  urllib.unquote(urllib.urlencode(params))
#
#         vlayer = QgsVectorLayer(uri, "poly_landmarks", "WFS")
#         self.assertTrue(vlayer.isValid())
#
#     def testOpenWMSLayer(self):
#         params = {
#             'service': 'wms',
#             'typename': 'Arc_Sample',
#             'crs': 'EPSG:4326',
#             'format': 'image/jpeg',
#             'certid': certfile,
#             'keyid': keyfile,
#             'issuerid': cafile
#         }
#         uri = 'http://localhost:8443/geoserver/wms?' +  urllib.unquote(urllib.urlencode(params))
#         rlayer = QgsRasterLayer(uri, 'Arc_Sample', 'wms')
#         self.assertTrue(rlayer.isValid())
#
# def suite():
#     suite = unittest.makeSuite(PKITests, 'test')
#     return suite
#
# def run_tests():
#     demo_test = unittest.TestLoader().loadTestsFromTestCase(PKITests)
#     unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(demo_test)
#===============================================================================