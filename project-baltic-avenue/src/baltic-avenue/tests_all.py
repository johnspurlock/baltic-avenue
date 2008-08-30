
import unittest

from baltic_utils import *

class AllTests( unittest.TestCase ):
   """ Class to test validation functions """
   
   def test_parse_url_path(self):
      #""" description goes here """
      self.assert_( parse_url_path('/bucket') == ('bucket',None,None))
      self.assert_( parse_url_path('/bucket/key') == ('bucket','key',None))
      self.assert_( parse_url_path('/bucket/','max-keys=1000') == ('bucket',None,'max-keys=1000'))
      self.assert_( parse_url_path('/asdf','location') == ('asdf',None,'location'))
    



def TestSuite():
   return unittest.makeSuite(AllTests)

if __name__ == '__main__':
   unittest.main()

