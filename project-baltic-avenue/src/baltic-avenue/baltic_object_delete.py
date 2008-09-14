from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *

class DeleteObjectOperation(S3Operation):
    
    

    def go(self, bucket, key):
        logging.info('DELETE bucket [%s] key [%s]' % (bucket,key))
        
        self.resource_type = 'OBJECT'
        
        if not self.check_auth(bucket,key):
            return
        
        
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        self.key = key
        
        # bucket does not exist
        if not self.bucket:
            self.error_no_such_bucket(bucket)
            return
        
        
        # bucket is owned by someone else
        if self.bucket.owner.id != self.requestor.id:
            self.error_access_denied()
            return
        
        # check acl
        if not self.check_permission(self.bucket.acl,'WRITE'): return
        
        # unencode the key
        key = url_unencode(key)
        
        # delete existing object (if exists)
        existing_oi = self.delete_object_if_exists(self.bucket,key)
        
        # delete common prefixes if necessary
        def delete_common_prefix_if_empty(cp):
            if not cp:
                return
            
            q1 = CommonPrefix.all().filter('common_prefix =',cp)
            q2 = ObjectInfo.all().filter('common_prefix =',cp)
            if len(q1.fetch(1)) == 0 and len(q2.fetch(1)) == 0:
                # the cp has no more related items or child cps, so safely delete it
                cp.delete()
                logging.info('deleted [%s]' % cp.full_name())
                
                delete_common_prefix_if_empty(cp.common_prefix) # check parent
        
        delete_common_prefix_if_empty(existing_oi.common_prefix)
            
        
        
            
        self.response.set_status(204)
    