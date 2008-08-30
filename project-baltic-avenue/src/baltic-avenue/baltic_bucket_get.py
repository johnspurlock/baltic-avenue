from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation

class GetBucketOperation(S3Operation):

    def go(self, bucket, query_string):
        logging.info('GET bucket [%s] (list bucket) query string [%s]' % (bucket, query_string))
        
        query_args = {}
        if query_string == 'location':
            query_args['location'] = ''
        if query_string == 'logging':
            query_args['logging'] = ''
        if query_string == 'acl':
            query_args['acl'] = ''
            
        if not self.check_auth(bucket=bucket,query_args=query_args):
            return
        
        
        
        
        self.response.set_status(200)
    
        self.response.headers['Content-Type'] = 'application/xml'
        
        # location constraint
        if query_args.has_key('location'):
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<LocationConstraint xmlns="http://s3.amazonaws.com/doc/2006-03-01/"/>')
            return
        
        # logging info
        if query_args.has_key('logging'):
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n\n<BucketLoggingStatus xmlns="http://s3.amazonaws.com/doc/2006-03-01/">\n<!--<LoggingEnabled><TargetBucket>myLogsBucket</TargetBucket><TargetPrefix>add/this/prefix/to/my/log/files/access_log-</TargetPrefix></LoggingEnabled>-->\n</BucketLoggingStatus>')
            return
        
        # acl
        if query_args.has_key('acl'):
            private_info = self.get_private_info()
            self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>')
            self.response.out.write(u'<ID>%s</ID>' % private_info.owner_id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % private_info.owner_display_name)
            self.response.out.write(u'</Owner><AccessControlList><Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="CanonicalUser">')
            self.response.out.write(u'<ID>%s</ID>' % private_info.owner_id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % private_info.owner_display_name)
            self.response.out.write(u'</Grantee><Permission>FULL_CONTROL</Permission></Grant></AccessControlList></AccessControlPolicy>')
            return
        



        
        
        # bucket listing
        self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?><ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
        self.response.out.write(u'<Name>%s</Name>' % bucket)
        self.response.out.write(u'<Prefix></Prefix><Marker></Marker><MaxKeys>1000</MaxKeys><Delimiter>/</Delimiter><IsTruncated>false</IsTruncated></ListBucketResult>')
        

