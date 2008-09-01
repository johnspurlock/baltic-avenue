from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *



class HeadObjectOperation(S3Operation):




    def go(self, bucket, key):
        logging.info('HEAD bucket [%s] key [%s]' % (bucket, key))
        
      
        if not self.check_auth(bucket,key):
            return
        
        
        b = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        
        # bucket does not exist
        if not b:
            self.response.set_status(404)
            return
        
        
        # bucket is owned by someone else
        if b.owner.id != self.requestor.id:
            self.response.set_status(403)
            return
        
        
        existing_oi = ObjectInfo.gql("WHERE ANCESTOR IS :1 and name1 = :2 LIMIT 1",b,key).get()
        if not existing_oi:
            self.response.set_status(404)
            return
        
        
        self.response.set_status(200)

        self.object_metadata_as_response_headers(existing_oi)

        

