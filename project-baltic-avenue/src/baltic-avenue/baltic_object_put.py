from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation, utc
from baltic_model import *
from baltic_utils import *
import md5
import base64

class PutObjectOperation(S3Operation):
    

    
    def go(self, bucket, key):
        logging.info('PUT bucket [%s] key [%s]' % (bucket,key))
        
        if not self.check_auth(bucket,key,query_args=self.request.params):
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
        
        
        # put acl
        if self.request.params.has_key('acl'):
            
            existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(b),key).get()
            
            object_acl = existing_oi.acl
            
            # check acl
            if not self.check_permission(object_acl,'WRITE_ACP'): return
                
            client_acl = parse_acl(self.request.body) 
            
            acl = ACL(owner=self.requestor)
            acl.put()
            
            for client_grant in client_acl.grants:
                principal = UserPrincipal.gql("WHERE id = :1",client_grant.grantee.id).get()
                grant = ACLGrant(acl=acl,permission=client_grant.permission,grantee=principal)
                grant.put()
            
            existing_oi.acl = acl
            existing_oi.put()
            
            
            self.response.set_status(200)
            return
        
        
        
        
        
        
        # check acl
        if not self.check_permission(b.acl,'WRITE'): return
        
        # unencode the key
        key = url_encode(key)
        
        # make sure the key is not too long
        max_size = 1024
        size = len(key)
        if size > max_size:
            self.error_key_too_long(max_size,size)
            return
        
        
        # ensure x-amz-acl is valid if provided
        canned_access_policy = self.request.headers.get('x-amz-acl')
        if canned_access_policy and canned_access_policy not in ['private','authenticated-read','public-read','public-read-write','log-delivery-write']:
            self.error_invalid_argument('x-amz-acl',canned_access_policy,'')
            return


        
        # load contents into buffer 
        contents = self.request.body
        
        # compute hash for etag and digest check
        m = md5.new()
        m.update(contents)
        
        # if content-md5 provided, check contents digest
        client_content_md5 = self.request.headers.get('content-md5')
        if client_content_md5 : 
            server_content_md5 = base64.standard_b64encode(m.digest())
            logging.info('client_content_md5 %s' % client_content_md5)
            logging.info('server_content_md5 %s' % server_content_md5)
            if server_content_md5 != client_content_md5:
                self.error_bad_digest(client_content_md5, server_content_md5)
                return
            
            
    
    
        # ok, everything checks out
        self.response.set_status(200)
          
        
        # delete existing object (if exists)
        self.delete_object_if_exists(b,key)
        

        # construct and save acl
        acl = ACL(owner=self.requestor)
        acl.put()
        
        canned_access_policy = canned_access_policy or 'private'
        if canned_access_policy == 'private':
            grant = ACLGrant(acl=acl,grantee=self.requestor,permission='FULL_CONTROL')
            grant.put()
        
        
        # construct and save object-info
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
                if not self.is_development_server() and h.lower() == 'content-type' and self.request.environ.get('HTTP_CONTENT_TYPE'):
                    value = self.request.environ.get('HTTP_CONTENT_TYPE')
                oi.__setattr__(h.lower(),value)

        oi.put()
        
        # save object contents
        oc = ObjectContents(
            parent=oi,
            object_info = oi,
            contents=contents)
        oc.put()
        
        
    