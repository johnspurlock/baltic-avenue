from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class DeleteBucketOperation(S3Operation):
    
    

    def go(self, bucket):
        logging.info('DELETE bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
        
        q = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        
        # bucket does not exist
        if not q:
            self.error_no_such_bucket(bucket)
            return

        # bucket is owned by someone else
        if q.owner.id != self.requestor.id:
            self.error_access_denied()
            return
        
        # delete it!
        if q:
            q.delete()
        
        self.response.set_status(204)
    