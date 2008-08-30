from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from google.appengine.ext import db


class DeleteBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('DELETE bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
        

        q = db.GqlQuery("SELECT * FROM Bucket WHERE name = :1 ",  bucket)
        
        results = q.fetch(10)
        
        for result in results:
            result.delete()
        
        self.response.set_status(204)
    