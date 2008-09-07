
import unittest

from baltic_utils import *



import random
import time

class AllTests( unittest.TestCase ):
    """ Class to test validation functions """
   
    def test_parse_url_path(self):
      #""" description goes here """
      self.assert_( parse_url_path('/bucket') == ('bucket',None))
      self.assert_( parse_url_path('/bucket/key') == ('bucket','key'))
      self.assert_( parse_url_path('/bucket/') == ('bucket',None))
      self.assert_( parse_url_path('/asdf') == ('asdf',None))
    
    def test_quote_xml(self):
       
       #print escape_xml('"cef7ccd89dacf1ced6f5ec91d759953f"')
       self.assert_(escape_xml('\"cef7ccd89dacf1ced6f5ec91d759953f\"') == "&quot;cef7ccd89dacf1ced6f5ec91d759953f&quot;")
       
       
    def test_string_to_sign_bytes(self):
       self.assert_( string_to_sign_bytes(u'\n\u1234') , '0a e1 88 b4')

    def test_parse_acl(self):
        
          
          acl_xml = u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>'
          acl_xml += u'<ID>id</ID>' 
          acl_xml +=  u'<DisplayName>display name</DisplayName>' 
          acl_xml +=   u'</Owner><AccessControlList><Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">'
          acl_xml +=   u'<ID>id</ID>' 
          acl_xml +=   u'<DisplayName>display name</DisplayName>' 
          acl_xml += u'</Grantee><Permission>FULL_CONTROL</Permission></Grant></AccessControlList></AccessControlPolicy>'
      
          acl = parse_acl(acl_xml)
         
          self.assert_('id'==acl.owner.id)
          self.assert_('display name'==acl.owner.display_name)
          self.assert_(1==len(acl.grants))
          self.assert_('id'==acl.grants[0].grantee.id)
          self.assert_('display name'==acl.grants[0].grantee.display_name)
          self.assert_('FULL_CONTROL'==acl.grants[0].permission)
        
          
    def test_temp(self): 
        
        s = None
        print long(s.strip()) if s and s.strip().isdigit() else 0
        
      #  print '123456789'[3:5] 
        
        #print time.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Sat, 03 May 2008 20:39:11 GMT
        
        #print len('dEEfIoqdj0kkSkoc81NuK4Q4BoYCZqunIL5y1bJ81zhx3dd0asGvCDZ0NrFMqoMU')
        #print '%16X' % random.getrandbits(4 * 16)
        #print '%64x' % random.getrandbits(4 * 64)
        


def TestSuite():
   return unittest.makeSuite(AllTests)

if __name__ == '__main__':
   unittest.main()

