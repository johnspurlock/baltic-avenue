from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *
import md5

class PutObjectOperation(S3Operation):
    
    def go(self, bucket, key):
        logging.info('PUT bucket [%s] key [%s]' % (bucket,key))
        
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
        if existing_oi:
            existing_oc = ObjectContents.gql("WHERE ANCESTOR IS :1 LIMIT 1", existing_oi).get()
            if existing_oc:
                existing_oc.delete()
            existing_oi.delete()
        
        
        contents = self.request.body
        
        
        m = md5.new()
        m.update(contents)

        
        acl = ACL(owner=self.requestor)
        acl.put()
        
        oi = ObjectInfo(
            parent=b,
            bucket=b,
            name1=key,
            last_modified=datetime.utcnow().replace(tzinfo=utc),
            etag = '"%s"' % m.hexdigest(),
            size=len(contents),
            owner = self.requestor,
            acl = acl)
        oi.put()
        
        oc = ObjectContents(
            parent=oi,
            object_info = oi,
            contents=contents)
        oc.put()
        
       
        self.response.set_status(200)
        
        
        
      
      