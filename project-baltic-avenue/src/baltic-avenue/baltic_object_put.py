from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *
from baltic_utils import *
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
        
        
        
        # unencode the key
        key = url_encode(key)
        
        # make sure the key is not too long
        max_size = 1024
        size = len(key)
        if size > max_size:
            self.error_key_too_long(max_size,size)
            return
        
        
        # delete existing object (if exists)
        self.delete_object_if_exists(b,key)
        
        
        # load contents into buffer 
        contents = self.request.body
        
        # compute hash for etag
        m = md5.new()
        m.update(contents)

        # save object
        acl = ACL(owner=self.requestor)
        acl.put()
        
        oi = ObjectInfo(
            parent=b,
            bucket=b,
            name1=key[0:500],
            name2=key[500:1000],
            name3=key[1000:1500],
            last_modified=datetime.utcnow().replace(tzinfo=utc),
            etag = '"%s"' % m.hexdigest(),
            size=len(contents),
            owner = self.requestor,
            acl = acl)
        
        
      
        #logging.info('\n' + '\n'.join(['%s: %s' % (h,self.request.headers[h]) for h in self.request.headers]))
        
        # save optional metadata as expando properties
        for h in self.request.headers:
            if h.lower().startswith('x-amz-meta-') or h.lower() in ['content-type','cache-control','content-disposition','expires','content-encoding']:
                value = self.request.headers.get(h)
                oi.__setattr__(h.lower(),value)

        oi.put()
        
        oc = ObjectContents(
            parent=oi,
            object_info = oi,
            contents=contents)
        oc.put()
        
       
        self.response.set_status(200)
        
        
        
      
      