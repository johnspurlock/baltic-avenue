from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class DeleteObjectOperation(S3Operation):
    
    

    def go(self, bucket, key):
        logging.info('DELETE bucket [%s] key [%s]' % (bucket,key))
        
        if not self.check_auth(bucket,key):
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
        
        
        # delete existing object (if exists)
        self.delete_object_if_exists(b,key)
            
        self.response.set_status(204)
    