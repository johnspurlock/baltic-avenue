from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *



class HeadObjectOperation(S3Operation):


    def go(self, bucket, key):
        logging.info('HEAD bucket [%s] key [%s]' % (bucket, key))
        
        self.resource_type = 'OBJECT'
        
        if not self.check_auth(bucket,key):
            return
        
        # locate bucket
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        self.key = key
        
        # bucket does not exist
        if not self.bucket:
            self.response.set_status(404)
            return
        
        

        # unencode the key
        key = url_unencode(key)
        
        # locate the object-info
        existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(self.bucket),key).get()
        if not existing_oi:
            self.response.set_status(404)
            return
        
        # assert READ
        if not self.check_permission(existing_oi.acl,'READ'): return
      
      
        # write out response headers
        self.response.set_status(200)
        self.object_metadata_as_response_headers(existing_oi)

        

