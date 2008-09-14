from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *

class HeadBucketOperation(S3Operation):

    def go(self, bucket):
        logging.info('HEAD bucket [%s]' % bucket)
        
        self.resource_type = 'BUCKET'
        
        if not self.check_auth(bucket):
            return
    
        
        # 200 if you own it (and have READ), 403 if someone else owns it, else 404
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        if self.bucket and self.bucket.owner.id == self.requestor.id and self.check_permission(self.bucket.acl,'READ'):
            self.response.set_status(200)
        elif self.bucket:
            self.response.set_status(403)
        else:
            self.response.set_status(404)
        
    