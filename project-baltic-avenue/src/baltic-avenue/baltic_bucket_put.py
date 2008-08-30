from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc, Bucket

class PutBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('PUT bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
        
        
        
        self.response.set_status(200)

        creation_date = datetime.utcnow().replace(tzinfo=utc)
        
        b = Bucket(name=bucket,creation_date=creation_date)
        
        b.put()
        
