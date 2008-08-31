from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *

class PutBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('PUT bucket [%s]' % bucket)
        
        if not self.check_auth(bucket):
            return
        
        
        
        q = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        
        # bucket is owned by someone else
        if q and q.owner.id != self.requestor.id:
            self.response.set_status(409)
            self.response.headers['Content-Type'] = 'application/xml'
            self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
            self.response.out.write( u'<Code>BucketAlreadyExists</Code>')
            self.response.out.write( u'<Message>The requested bucket name is not available. The bucket namespace is shared by all users of the system. Please select a different name and try again.</Message>')
            self.response.out.write( u'<RequestId>9320BB242B9B949C</RequestId>')
            self.response.out.write( u'<BucketName>%s</BucketName>' %  bucket)
            self.response.out.write( u'<HostId>+nagCZ1y4Me+rv3TKeHIvY3axqaQTlLaS3p7iqSZDc3JYpG4+ae8HJY2XYhlUkSq</HostId>')
            self.response.out.write( u'</Error>')
            return
        
        
       
        self.response.set_status(200)
        
        # if you already own it, it succeeds!
        if q:
            return
        
        
        # create the bucket
        creation_date = datetime.utcnow().replace(tzinfo=utc)
        
        owner = self.requestor
        acl = ACL(owner=owner)
        acl.put()
        
        b = Bucket(name1=bucket,creation_date=creation_date,owner=owner,acl=acl)
        
        b.put()
        
