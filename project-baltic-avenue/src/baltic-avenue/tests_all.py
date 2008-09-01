
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
    

   def test_quote_xml(self):
       
       #print escape_xml('"cef7ccd89dacf1ced6f5ec91d759953f"')
       self.assert_(escape_xml('\"cef7ccd89dacf1ced6f5ec91d759953f\"') == "&quot;cef7ccd89dacf1ced6f5ec91d759953f&quot;")
       
       
   def test_string_to_sign_bytes(self):
       self.assert_( string_to_sign_bytes(u'\n\u1234') , '0a e1 88 b4')

def TestSuite():
   return unittest.makeSuite(AllTests)

if __name__ == '__main__':
   unittest.main()

