from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *

class PutBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('PUT bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return


        b = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        # bucket is owned by someone else
        if b and b.owner.id != self.requestor.id:
            self.error_bucket_already_exists(bucket)
            return
        
        
       
        self.response.set_status(200)
        
        # if you already own it, it succeeds!
        if b:
            return
        
        
        # create the bucket
        creation_date = datetime.utcnow().replace(tzinfo=utc)
        
        owner = self.requestor
        acl = ACL(owner=owner)
        acl.put()
        
        b = Bucket(name1=bucket,creation_date=creation_date,owner=owner,acl=acl)
        b.put()
        
