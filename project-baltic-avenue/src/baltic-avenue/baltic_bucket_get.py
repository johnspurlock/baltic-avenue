from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *



class GetBucketOperation(S3Operation):

    def go(self, bucket):
        logging.info('GET bucket [%s] (list bucket) query string [%s]' % (bucket, self.request.params))
        
        
        if not self.check_auth(bucket=bucket,query_args=self.request.params):
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
        
        
        # list it!
        
        self.response.set_status(200)
    
        self.response.headers['Content-Type'] = 'application/xml'
        
        # location constraint
        if self.request.params.has_key('location'):
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<LocationConstraint xmlns="http://s3.amazonaws.com/doc/2006-03-01/"/>')
            return
        
        # logging info
        if self.request.params.has_key('logging'):
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n\n<BucketLoggingStatus xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n<!--<LoggingEnabled><TargetBucket>myLogsBucket</TargetBucket><TargetPrefix>add/this/prefix/to/my/log/files/access_log-</TargetPrefix></LoggingEnabled>-->\n</BucketLoggingStatus>')
            return
        
        # return acl
        if self.request.params.has_key('acl'):
            bucket_acl = b.acl
            
            # check acl
            if not self.check_permission(bucket_acl,'READ_ACP'): return
            
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>')
            self.response.out.write(u'<ID>%s</ID>' % bucket_acl.owner.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % bucket_acl.owner.display_name)
            self.response.out.write(u'</Owner><AccessControlList>')
            
            
            for grant in bucket_acl.grants:
                self.response.out.write(u'<Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">')
                self.response.out.write(u'<ID>%s</ID>' % grant.grantee.id)
                self.response.out.write(u'<DisplayName>%s</DisplayName>' % grant.grantee.display_name)
                self.response.out.write(u'</Grantee><Permission>%s</Permission></Grant>' % grant.permission)
                
                
            
            self.response.out.write(u'</AccessControlList></AccessControlPolicy>')
            return
        
    
        # check acl
        if not self.check_permission(b.acl,'READ'): return
            


        
       
        # validate and clean args
        
        # validate max-keys
        client_max_keys = self.request.params.get('max-keys')
        if client_max_keys:
            if not client_max_keys.strip().isdigit():
                self.error_invalid_argument_not_integer('max-keys',client_max_keys)
                return
            client_max_keys = long(client_max_keys.strip())
            if client_max_keys < 0 or client_max_keys > 2147483647:
                self.error_invalid_argument_integer_range('maxKeys',client_max_keys)
                return
        max_keys = min(client_max_keys or 1001,1000)
        
        
        # validate and unencode delimiter
        delimiter = url_unencode(self.request.params.get('delimiter') or '')
        
        # validate and unencode prefix
        prefix = url_unencode(self.request.params.get('prefix') or '')
        
        # validate and unencode marker
        marker = url_unencode(self.request.params.get('marker') or '')
        
        is_truncated = False
        next_marker = None
        
        ois = []
        cps = []
        if max_keys > 0:
            # return ordered by key name
            q = ObjectInfo.all().ancestor(b).order('name1').order('name2').order('name3') 
            
            # NEW WAY filter on parent cp
            parent_cp_full_name = compute_common_prefix(prefix)
            q2 = CommonPrefix.all().filter('bucket =',b)
            self.add_key_query_filters(q2,parent_cp_full_name)
            parent_cp = q2.get()
            
            if parent_cp:
                         
                # our single allowed filter will be based on common-prefix
                q.filter('common_prefix = ',parent_cp)
                
                    
                # if delimiter provided, grab all possible cps
                possible_cps = []
                if len(delimiter) > 0:
                    possible_cps = list(parent_cp.children)
                    possible_cps.sort(key=lambda cp: cp.full_name())

                
               
                # now fetch and post-process
                for item in combine(q,possible_cps,lambda x:x.full_name()):
                    
                    # only return items that start with the prefix (if provided)
                    if len(prefix) == 0 or item.full_name().startswith(prefix):  
                        
                        # only return items that are after the marker (if provided)
                        if len(marker)==0 or item.full_name() > marker:
                            
                            # compute common-prefix if delimiter supplied
                            cp = None
                            oi = None
                            
                           
                            if isinstance(item,CommonPrefix):
                                cp = item
                            else:
                                oi = item
                                    
                                    
        
                            # if we get to this point, we are about to add a cp or an oi
                            if len(ois)+len(cps) == max_keys:
                                is_truncated = True
                                if len(delimiter) > 0:
                                    next_marker = max(ois[-1],cps[-1])
                                break
                            
                            # add the new oi or cp to the result list
                            if cp:
                                cps.append(cp)
                            else:
                                ois.append(oi)

                                            
    


        
        # write out the response
        self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
        self.response.out.write(u'<Name>%s</Name>' % bucket)
        self.response.out.write(u'<Prefix>%s</Prefix>' % prefix)
        self.response.out.write(u'<Marker>%s</Marker>' % marker)
        if next_marker:
            self.response.out.write(u'<NextMarker>%s</NextMarker>' % next_marker.full_name())
        self.response.out.write(u'<MaxKeys>%s</MaxKeys>' % max_keys)
        self.response.out.write(u'<Delimiter>%s</Delimiter>' % delimiter)
        self.response.out.write(u'<IsTruncated>%s</IsTruncated>' % is_truncated)
    
        for oi in ois:
            self.response.out.write(u'<Contents>')
            self.response.out.write(u'<Key>%s</Key>' % oi.full_name())
            self.response.out.write(u'<LastModified>%s</LastModified>' % date_format_1(oi.last_modified))
            self.response.out.write(u'<ETag>%s</ETag>' % escape_xml(oi.etag))
            self.response.out.write(u'<Size>%s</Size>' % oi.size)
            self.response.out.write(u'<Owner>')
            self.response.out.write(u'<ID>%s</ID>' % oi.owner.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>'% oi.owner.display_name)
            self.response.out.write(u'</Owner><StorageClass>STANDARD</StorageClass>')
            self.response.out.write(u'</Contents>')

        if len(cps) > 0:
            self.response.out.write(u'<CommonPrefixes>')
            for cp in cps:
                self.response.out.write(u'<Prefix>%s</Prefix>' % cp.full_name())
            self.response.out.write(u'</CommonPrefixes>')

        self.response.out.write(u'</ListBucketResult>')
        

