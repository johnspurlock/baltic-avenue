from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class DeleteBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('DELETE bucket [%s]' % bucket)
        
        self.resource_type = 'BUCKET'
        
        if not self.check_auth(bucket):
            return
        
        # locate bucket
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        
        # bucket does not exist
        if not self.bucket:
            self.error_no_such_bucket(bucket)
            return

        # bucket is owned by someone else
        if self.bucket.owner.id != self.requestor.id:
            self.error_access_denied()
            return
        
        # assert WRITE
        if not self.check_permission(self.bucket.acl,'WRITE'): return
        
        
        # make sure the bucket is empty
        is_empty = ObjectInfo.gql("WHERE ANCESTOR IS :1 LIMIT 1",self.bucket).count() == 0
        if not is_empty:
            self.error_bucket_not_empty(bucket)
            return
        
        
        # delete it!
        for cp in CommonPrefix.all().filter('bucket =',self.bucket):
            cp.delete()
        self.bucket.acl.delete()
        self.bucket.delete()
        

        # expected response for delete
        self.response.set_status(204)
    