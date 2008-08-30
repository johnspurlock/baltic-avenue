from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from google.appengine.ext import db

class HeadBucketOperation(S3Operation):

    def go(self, bucket):
        logging.info('HEAD bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
    
        
        # 200 if you own it, 403 if someone else owns it, else 404
        q = db.GqlQuery("SELECT * FROM Bucket WHERE name = :1 ",  bucket)
        if (q.count() == 1):
            self.response.set_status(200)
            return;
        
        self.response.set_status(404)
        
    