from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *


class GetObjectOperation(S3Operation):
    
    

    def go(self, bucket, key):
        logging.info('GET bucket [%s] key [%s]' % (bucket,key))
        
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
        
        
        existing_oi = ObjectInfo.gql("WHERE ANCESTOR IS :1 and name1 = :2 LIMIT 1",b,key).get()
        if not existing_oi:
            self.error_no_such_key(key)
            return
            
            
        existing_oc = ObjectContents.gql("WHERE ANCESTOR IS :1 LIMIT 1", existing_oi).get()
        
        
        self.response.set_status(200)
        #self.response.headers['Content-Type'] = 'temp'
        self.response.out.write(existing_oc.contents)
        
        
        
        
    