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
        
        self.resource_type = 'OBJECT'
        
        if not self.check_auth(bucket,key,query_args=self.request.params):
            return
        
        
        
        self.bucket = Bucket.gql("WHERE name1 = :1 ",  bucket).get()
        self.key = key
        
        # bucket does not exist
        if not self.bucket:
            self.error_no_such_bucket(bucket)
            return
        
        # put acl
        if self.request.params.has_key('acl'):
            self.resource_type = 'ACL'
            existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(self.bucket),key).get()
            
            object_acl = existing_oi.acl
            
            # check acl
            if not self.check_permission(object_acl,'WRITE_ACP'): return
                
            acl = self.read_acl()
            
            existing_oi.acl = acl
            existing_oi.put()
            
            self.response.set_status(200)
            return
        
        
        
        
        
        
        # check acl
        if not self.check_permission(self.bucket.acl,'WRITE'): return
        
        # unencode the key
        key = url_unencode(key)
        
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
        
        # if the content is larger than 1048406, appspot might reject it (quota)
        max_size = 1048406
        if len(contents) > max_size:
            self.error_entity_too_large(len(contents),max_size)
            return
            
    
    
    
    
    
        # ok, everything checks out
        self.response.set_status(200)
          
        
        # delete existing object (if exists)
        old_oi = self.delete_object_if_exists(self.bucket,key)
        
        # construct and save acl
        acl = ACL(owner=self.requestor)
        acl.put()
        
        canned_access_policy = canned_access_policy or 'private'
        if canned_access_policy in ['private','public-read','public-read-write']:
            grant = ACLGrant(acl=acl,grantee=self.requestor,permission='FULL_CONTROL')
            grant.put()
        if canned_access_policy in ['public-read','public-read-write']:
            grant = ACLGrant(acl=acl,grantee=self.all_users,permission='READ')
            grant.put()
        if canned_access_policy in ['public-read-write']:
            grant = ACLGrant(acl=acl,grantee=self.all_users,permission='WRITE')
            grant.put()
        
        # locate or create common prefix
        cp = old_oi.common_prefix if old_oi else None
        if not cp:
            def ensure_exists(full_name):
                q = CommonPrefix.all()
                q = q.filter('bucket = ',self.bucket)
                q =  self.add_key_query_filters(q,full_name)
                existing_cp = q.get()
                if existing_cp:
                    return existing_cp
                
                if full_name == '':
                    new_cp = CommonPrefix(bucket=self.bucket,name1='',name2='',name3='')
                    new_cp.put()
                    logging.info('put [%s]' % new_cp.full_name())
                    return new_cp
                
                parent_full_name = compute_common_prefix(full_name[:-1])
                parent_cp = ensure_exists(parent_full_name)
                
                new_cp = CommonPrefix(
                    bucket=self.bucket, 
                    common_prefix=parent_cp,
                    name1=full_name[0:500],
                    name2=full_name[500:1000],
                    name3=full_name[1000:1500])
                new_cp.put()
                logging.info('put [%s]' % new_cp.full_name())
                return new_cp
                
            cp_full_name = compute_common_prefix(key)
            cp = ensure_exists(cp_full_name)
            

        # construct and save object-info
        oi = ObjectInfo(
            parent=self.bucket,
            bucket=self.bucket,
            name1=key[0:500],
            name2=key[500:1000],
            name3=key[1000:1500],
            last_modified=datetime.utcnow().replace(tzinfo=utc),
            etag = '"%s"' % m.hexdigest(),
            size=len(contents),
            owner = self.requestor,
            acl = acl,
            common_prefix = cp)
        
        
      
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
        
        
    