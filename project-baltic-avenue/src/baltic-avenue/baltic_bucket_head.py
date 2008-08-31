from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *

class HeadBucketOperation(S3Operation):

    def go(self, bucket):
        logging.info('HEAD bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
    
        
        # 200 if you own it, 403 if someone else owns it, else 404
        q = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        if q and q.owner.id == self.requestor.id:
            self.response.set_status(200)
        elif q:
            self.response.set_status(403)
        else:
            self.response.set_status(404)
        
    