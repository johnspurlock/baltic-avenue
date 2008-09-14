from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *
from baltic_utils import *


class PutBucketOperation(S3Operation):
    
    def go(self, bucket):
        logging.info('PUT bucket [%s]' % bucket)
        
        if not self.check_auth(bucket,query_args=self.request.params):
            return

        b = Bucket.gql("WHERE name1 = :1 ",  bucket).get()

        # put acl
        if self.request.params.has_key('acl'):
            
            # check acl
            if not self.check_permission(b.acl,'WRITE_ACP'): return
                
            acl = self.read_acl()
            
            b.acl = acl
            b.put()
            
            self.response.set_status(200)
            return
        
        
        
        # bucket is owned by someone else
        if b and b.owner.id != self.requestor.id:
            self.error_bucket_already_exists(bucket)
            return
        
        # check acl
        if b and not self.check_permission(b.acl,'WRITE'): return
        
        
        self.response.set_status(200)
        
        # if you already own it, it succeeds!
        if b:
            return
        
        
       
        # create the acl
        creation_date = datetime.utcnow().replace(tzinfo=utc)
        
        owner = self.requestor
        acl = ACL(owner=owner)
        acl.put()
        grant = ACLGrant(acl=acl,grantee=owner,permission='FULL_CONTROL')
        grant.put()
        
        
        # create the bucket
        b = Bucket(name1=bucket,creation_date=creation_date,owner=owner,acl=acl)
        b.put()
        
