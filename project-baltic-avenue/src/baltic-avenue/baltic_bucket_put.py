from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *
from baltic_utils import *


class PutBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('PUT bucket [%s]' % bucket)
        
        self.resource_type = 'BUCKET'
        
        if not self.check_auth(bucket,query_args=self.request.params):
            return

        # locate bucket
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()

        # bucket is owned by someone else
        if self.bucket and self.bucket.owner.id != self.requestor.id:
            self.error_bucket_already_exists(bucket)
            return
        
        # put acl
        if self.request.params.has_key('acl'):
            self.resource_type = 'ACL'
            
            if not self.bucket:
                self.error_no_such_bucket(bucket)
                return
                    
            
            # assert WRITE_ACP
            if not self.check_permission(self.bucket.acl,'WRITE_ACP'): return
            
            # parse acl and associate with bucket
            acl = self.read_acl()
            self.bucket.acl = acl
            self.bucket.put()
            
            self.response.set_status(200)
            return
        
        
        

        
        # assert WRITE
        if self.bucket and not self.check_permission(self.bucket.acl,'WRITE'): return
        
        
        self.response.set_status(200)
        
        # if you already own it, it succeeds!
        if self.bucket:
            return
        
        
       
        # create the acl
        creation_date = datetime.utcnow().replace(tzinfo=utc)
        
        owner = self.requestor
        acl = ACL(owner=owner)
        acl.put()
        grant = ACLGrant(acl=acl,grantee=owner,permission='FULL_CONTROL')
        grant.put()
        
        
        # create the bucket
        self.bucket = Bucket(name1=bucket,creation_date=creation_date,owner=owner,acl=acl)
        self.bucket.put()
        
