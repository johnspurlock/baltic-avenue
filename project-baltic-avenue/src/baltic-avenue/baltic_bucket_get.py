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
        
        # acl
        if self.request.params.has_key('acl'):
            temp = self.requestor
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>')
            self.response.out.write(u'<ID>%s</ID>' % temp.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % temp.display_name)
            self.response.out.write(u'</Owner><AccessControlList><Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">')
            self.response.out.write(u'<ID>%s</ID>' % temp.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % temp.display_name)
            self.response.out.write(u'</Grantee><Permission>FULL_CONTROL</Permission></Grant></AccessControlList></AccessControlPolicy>')
            return
        



        
       
        # bucket listing
        
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
        
            
            
        max_keys = min(client_max_keys,1000)
        delimiter = ''
        prefix = self.request.params.get('prefix') or ''
        marker = ''
        is_truncated = False
        
        items = []
        if max_keys > 0:
            # return ordered by key name
            q = ObjectInfo.all().ancestor(b).order('name1').order('name2').order('name3') 
            
            # filter as much as possible on the backend
            # appengine only allows one neq filter, so we'll filter on name1
            if len(prefix) > 0:
                q = q.filter('name1 >=',prefix).filter('name1 <',prefix + u'\xEF\xBF\xBD')
            
            # now fetch and post-process
            for oi in q:    # using query as an iterable should lazy load in chunks, not buffer all objects...
                
                if len(prefix) == 0 or oi.name1.startswith(prefix):
                    if len(items) == max_keys:
                        is_truncated = True
                        break
                    items.append(oi)


        
        
        self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
        self.response.out.write(u'<Name>%s</Name>' % bucket)
        self.response.out.write(u'<Prefix>%s</Prefix>' % prefix)
        self.response.out.write(u'<Marker>%s</Marker>' % marker)
        self.response.out.write(u'<MaxKeys>%s</MaxKeys>' % max_keys)
        self.response.out.write(u'<Delimiter>%s</Delimiter>' % delimiter)
        self.response.out.write(u'<IsTruncated>%s</IsTruncated>' % is_truncated)
    

        for oi in items:
            self.response.out.write(u'<Contents>')
            self.response.out.write(u'<Key>%s</Key>' % (oi.name1 + oi.name2 + oi.name3))
            self.response.out.write(u'<LastModified>%s</LastModified>' % date_format_1(oi.last_modified))
            self.response.out.write(u'<ETag>%s</ETag>' % escape_xml(oi.etag))
            self.response.out.write(u'<Size>%s</Size>' % oi.size)
            self.response.out.write(u'<Owner>')
            self.response.out.write(u'<ID>%s</ID>' % oi.owner.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>'% oi.owner.display_name)
            self.response.out.write(u'</Owner><StorageClass>STANDARD</StorageClass></Contents>')

          

        self.response.out.write(u'</ListBucketResult>')
        

