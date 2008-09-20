
import unittest
import random
import time

from baltic_utils import *


class AllTests( unittest.TestCase ):
   
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
          acl_xml +=   u'</Owner><AccessControlList>'
          
          
          acl_xml +=  u'<Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">'
          acl_xml +=   u'<ID>id</ID>' 
          acl_xml +=   u'<DisplayName>display name</DisplayName>' 
          acl_xml += u'</Grantee><Permission>FULL_CONTROL</Permission></Grant>'
          
          acl_xml +=  u'<Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="Group">'
          acl_xml +=   u'<URI>http://uri</URI>' 
          acl_xml += u'</Grantee><Permission>READ</Permission></Grant>'
          
          acl_xml += u'</AccessControlList></AccessControlPolicy>'
      
          acl = parse_acl(acl_xml)
         
          self.assert_('id'==acl.owner.id)
          self.assert_('display name'==acl.owner.display_name)
          self.assert_(2==len(acl.grants))
          
          self.assert_('CanonicalUser'==acl.grants[0].grantee.type)
          self.assert_('id'==acl.grants[0].grantee.id)
          self.assert_('display name'==acl.grants[0].grantee.display_name)
          self.assert_('FULL_CONTROL'==acl.grants[0].permission)
        
          self.assert_('Group'==acl.grants[1].grantee.type)
          self.assert_('http://uri'==acl.grants[1].grantee.uri)
          self.assert_('READ'==acl.grants[1].permission)
          
          
          
    def test_compute_common_prefix(self):
        
        #print compute_common_prefix('a/a')
        self.assert_('a/a/'==compute_common_prefix('a/a/'))
        self.assert_('a/'==compute_common_prefix('a/a'))
        self.assert_('a/'==compute_common_prefix('a/'))
        self.assert_(''==compute_common_prefix('a'))
        self.assert_('/'==compute_common_prefix('/'))
        
        
        
    def test_temp(self): 
        
        
        def y():
            print "1"
            yield 1
            print "3"
            yield 3
            print "5"
            yield 5
        
        s = combine(y(),[2,4,6],lambda x:x)
        print 'ASDF %s' % list(s)
        #print long(s.strip()) if s and s.strip().isdigit() else 0
        
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

