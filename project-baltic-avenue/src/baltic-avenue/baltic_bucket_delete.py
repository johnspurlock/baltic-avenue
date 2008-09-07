from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class DeleteBucketOperation(S3Operation):
    
    

    def go(self, bucket):
        logging.info('DELETE bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
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
        
        # check acl
        if not self.check_permission(b.acl,'WRITE'): return
        
        
        # make sure the bucket is empty
        is_empty = ObjectInfo.gql("WHERE ANCESTOR IS :1 LIMIT 1",b).count() == 0
        if not is_empty:
            self.error_bucket_not_empty(bucket)
            return
        
        
        # delete it!
        b.acl.delete()
        b.delete()
            
        
        self.response.set_status(204)
    