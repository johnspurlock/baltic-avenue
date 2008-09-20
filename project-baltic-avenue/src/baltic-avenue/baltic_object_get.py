from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *

class GetObjectOperation(S3Operation):
    

    def go(self, bucket, key):
        logging.info('GET bucket [%s] key [%s] request-params [%s]' % (bucket,key,self.request.params))
        
        self.resource_type = 'OBJECT'
        
        if not self.check_auth(bucket,key,query_args=self.request.params):
            return
        
        # locate bucket
        self.bucket = Bucket.gql("WHERE name1 = :1 ", bucket).get()
        self.key = key
        
        # bucket does not exist
        if not self.bucket:
            self.error_no_such_bucket(bucket)
            return
        
        
        # unencode the key
        key = url_unencode(key)
        
        # locate the object-info
        existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(self.bucket),key).get()
        if not existing_oi:
            self.error_no_such_key(key)
            return
            
            
            
        # common response
        self.response.set_status(200)
        self.response.headers['Content-Type'] = 'application/xml'
            
        # get acl
        object_acl = existing_oi.acl
        if self.request.params.has_key('acl'):   
            self.resource_type = 'ACL'
            
            # assert READ_ACP
            if not self.check_permission(object_acl,'READ_ACP'): return

            self.write_acl(object_acl)
            return
            
            
            
        # assert READ
        if not self.check_permission(object_acl,'READ'): return
        
        
        # get the object-contents
        existing_oc = ObjectContents.gql("WHERE ANCESTOR IS :1 LIMIT 1", existing_oi).get()
        
        # write out the response
        self.response.set_status(200)
        self.object_metadata_as_response_headers(existing_oi)
        self.response.out.write(existing_oc.contents)
        
        