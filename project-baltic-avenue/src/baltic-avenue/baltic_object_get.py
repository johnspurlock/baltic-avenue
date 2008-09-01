from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class GetObjectOperation(S3Operation):
    
    

    def go(self, bucket, key, query_string):
        logging.info('GET bucket [%s] key [%s] query-string [%s]' % (bucket,key,query_string))
        
        query_args = {}
        if query_string == 'acl':
            query_args['acl'] = ''
            
        if not self.check_auth(bucket,key,query_args=query_args):
            return
        
        
        b = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        # bucket does not exist
        if not b:
            self.error_no_such_bucket(bucket)
            return
        
        
        # bucket is owned by someone else
        if b.owner.id != self.requestor.id:
            self.error_access_denied()
            return
        
        
        existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(b),key).get()
        if not existing_oi:
            self.error_no_such_key(key)
            return
            
            
            
        # acl
        if query_args.has_key('acl'):   
            temp = self.requestor
            self.response.headers['Content-Type'] = 'application/xml'
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>')
            self.response.out.write(u'<ID>%s</ID>' % temp.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % temp.display_name)
            self.response.out.write(u'</Owner><AccessControlList><Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">')
            self.response.out.write(u'<ID>%s</ID>' % temp.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % temp.display_name)
            self.response.out.write(u'</Grantee><Permission>FULL_CONTROL</Permission></Grant></AccessControlList></AccessControlPolicy>')
            return
            
            
            
        existing_oc = ObjectContents.gql("WHERE ANCESTOR IS :1 LIMIT 1", existing_oi).get()
        
        
        self.response.set_status(200)
        self.object_metadata_as_response_headers(existing_oi)
        self.response.out.write(existing_oc.contents)
        
        
        
        
    