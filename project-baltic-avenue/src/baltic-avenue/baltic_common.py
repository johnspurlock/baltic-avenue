from datetime import tzinfo, timedelta, datetime
from baltic_model import *
from baltic_utils import *

import base64
import urllib
import hmac
import sha
import logging
import re
import random

import pprint
import os

ZERO = timedelta(0)
HOUR = timedelta(hours=1)



# A UTC class.

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

    def __repr__(self):
        return 'UTC'
    

utc = UTC()




class S3Operation():

    
    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.requestor = None

        self.request_id = '%16X' % random.getrandbits(4 * 16)
        self.host_id = '%64x' % random.getrandbits(4 * 64)
        
        self.response.headers['x-amz-request-id'] = self.request_id
        self.response.headers['x-amz-id-2'] = self.host_id


        self._all_users = None
    def get_all_users(self):
        if not self._all_users:
            self._all_users = GroupPrincipal.all().filter('uri =','http://acs.amazonaws.com/groups/global/AllUsers').get()
            logging.debug('loaded self._all_users')
        return  self._all_users

    all_users = property(get_all_users)
     
    
        
    def go2(self,*args):
        try:
            self.go(args)
        finally:
            
            return
            from datetime import datetime
        
            bucket = args[0]
        
            b = Bucket.gql('WHERE name1 = :1',bucket).get()
        
            bucket_owner = b.owner.id if b else '???'
            time = datetime.utcnow()   # time in which request was received
            remote_ip = self.request.remote_addr
            requestor = self.requestor
            request_id = self.request_id
            operation = 'REST.PUT.OBJECT'
            key = args[1] if len(args) > 1 else None
            request_uri= '%s %s' % (self.request.method, self.request.path_qs)
            status = self.response._Response__status[0]     # response.status_code, response.status_int don't work!
            error_code = 'NoSuchBucket'
            bytes_sent = len(self.response.out.getvalue()) # out = StringIO
            object_size = '???' #the total size of the object in question
            total_time = 70  # millis
            turnaround_time = 70  # last bytes of request to first byte of response
            referrer = self.request.referrer
            user_agent = self.request.user_agent
            
            data = {'bucket_owner':bucket_owner,'bucket':bucket,'time':time,'remote_ip':remote_ip,
                    'requestor':requestor,'request_id':request_id,'operation':operation,'key':key,
                    'request_uri':request_uri,'status':status,'error_code':error_code,
                    'bytes_sent':bytes_sent,'object_size':object_size,'total_time':total_time,
                    'turnaround_time':turnaround_time,'referrer':referrer,'user_agent':user_agent}
        
            s = '\n' + '\n'.join(map(lambda x:'%s:%s'%(x,data[x]),data))
        
            logging.info(s)
       
       
    def write_acl(self, acl):
        self.response.out.write(u'<?xml version="1.0" encoding="UTF-8"?>\n<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Owner>')
        self.response.out.write(u'<ID>%s</ID>' % acl.owner.id)
        self.response.out.write(u'<DisplayName>%s</DisplayName>' % acl.owner.display_name)
        self.response.out.write(u'</Owner><AccessControlList>')
        
        for grant in acl.grants:
            type = 'Group' if isinstance(grant,GroupPrincipal) else 'CanonicalUser'
            
            self.response.out.write(u'<Grant><Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="%s">'% type)
            self.response.out.write(u'<ID>%s</ID>' % grant.grantee.id)
            self.response.out.write(u'<DisplayName>%s</DisplayName>' % grant.grantee.display_name)
            if type == 'Group':
                self.response.out.write(u'<URI>%s</URI>' % grant.grantee.uri)
            self.response.out.write(u'</Grantee><Permission>%s</Permission></Grant>' % grant.permission)
            
        self.response.out.write(u'</AccessControlList></AccessControlPolicy>')
  
            
    def read_acl(self):
        client_acl = parse_acl(self.request.body) 
        
        acl = ACL(owner=self.requestor)
        acl.put()
        
        for client_grant in client_acl.distinct_grants():
            principal = None
            if client_grant.grantee.type == 'Group':
                principal = GroupPrincipal.all().filter('uri =',client_grant.grantee.uri).get()
                logging.debug('found group-principal [%s] from uri = [%s]'%(principal,client_grant.grantee.uri))
            else:                    
                principal = UserPrincipal.all().filter("id =",client_grant.grantee.id).get()
                logging.debug('found user-principal [%s] from id = [%s]'%(principal,client_grant.grantee.id))
           
            grant = ACLGrant(acl=acl,permission=client_grant.permission,grantee=principal)
            grant.put()
        return acl
    
    # generates the aws canonical string for the given parameters
    def canonical_string(self, method, bucket="", key=None, query_args={}, headers={}, expires=None):
        
        
        AMAZON_HEADER_PREFIX = 'x-amz-'
        
        #for e in self.request.environ:
        #    logging.info('%s %s' % (e, self.request.environ[e]))
        
        
        interesting_headers = {}
        for header_key in headers:
            #logging.info('header_key %s' % header_key)
            lk = header_key.lower()
            if lk in ['content-md5','date','content-type'] or lk.startswith(AMAZON_HEADER_PREFIX):
                if not self.is_development_server() and lk == 'content-type':
                    interesting_headers[lk] = self.request.environ.get('HTTP_CONTENT_TYPE') or ''
                else:
                    interesting_headers[lk] = headers[lk].strip() 
    
        # workaround for dev_appserver defaulting content-type to application/x-www-form-urlencoded
        # assume that form-urlencoded means none provided
        if interesting_headers.has_key('content-type') and interesting_headers['content-type'] == 'application/x-www-form-urlencoded':
            del interesting_headers['content-type']
            
        
    
        # these keys get empty strings if they don't exist
        if not interesting_headers.has_key('content-type'):
            interesting_headers['content-type'] = ''
        if not interesting_headers.has_key('content-md5'):
            interesting_headers['content-md5'] = ''
    
        # just in case someone used this.  it's not necessary in this lib.
        if interesting_headers.has_key('x-amz-date'):
            interesting_headers['date'] = ''
    
        # if you're using expires for query string auth, then it trumps date
        # (and x-amz-date)
        if expires:
            interesting_headers['date'] = str(expires)
    
        sorted_header_keys = interesting_headers.keys()
        sorted_header_keys.sort()
    
        buf = "%s\n" % method
        for header_key in sorted_header_keys:
            if header_key.startswith(AMAZON_HEADER_PREFIX):
                buf += "%s:%s\n" % (header_key, interesting_headers[header_key])
            else:
                buf += "%s\n" % interesting_headers[header_key]
    
    
        # always append /
        buf += '/'
    
        # append the bucket if it exists
        if bucket != '':
            buf += "%s" % bucket 


        logging.info('self.request.path_qs %s' % self.request.path_qs)
        
        p = self.request.path.replace('%25','%')
        logging.info('self.request.pathp %s' % p)
        
        logging.info('self.request.url %s' % self.request.url)
        
        logging.info('self.request.environ:\n%s', pprint.pformat(self.request.environ))
        
        logging.info('key %s' % key)
        
        # add the key
        if key:
            buf +=  '/' + (key if self.request.environ.get('HTTP_USER_AGENT') == 'gzip(gfe)' else url_encode(key))
        elif self.request.path.endswith('/') and len(self.request.path) > 1:
        #elif self.request.path != '/':
            buf +=  '/'
        # handle special query string arguments
    
        if query_args.has_key("acl"):
           # if not key:
            #    buf += '/'  # only add a trailing slash for acl???
            buf += "?acl"
        elif query_args.has_key("torrent"):
            buf += "?torrent"
        elif query_args.has_key("logging"):
            buf += "?logging"
        elif query_args.has_key("location"):
            buf += "?location"
    

    
    
        return buf

    
    


    # computes the base64'ed hmac-sha hash of the canonical string and the secret
    # access key, optionally urlencoding the result
    def encode(self, aws_secret_access_key, str, urlencode=False):
        b64_hmac = base64.encodestring(hmac.new(aws_secret_access_key, str, sha).digest()).strip()
        if urlencode:
            return urllib.quote_plus(b64_hmac)
        else:
            return b64_hmac

    

    def check_auth(self, bucket='', key=None, query_args = {}):
        
        logging.info('check_auth [%s]' % os.environ.get("HTTP_AUTHORIZATION"))
        
        # check auth header present
        client_auth = os.environ.get("HTTP_AUTHORIZATION")
        if not client_auth:
            # if no auth header provided, this is a public request
            self.requestor = self.all_users
            return True
        
        logging.info('client_auth [%s]' % client_auth)
        
        m = re.match('^AWS ([^:]+):([^:]+)$',client_auth)
        if not m:
            self.error_generic(400,'InvalidHeader','Authorization header is not in the correct format')
            return False
        
        
        client_aws_key = m.group(1)
        client_aws_secrethash = m.group(2)
        
        
        self.requestor = UserPrincipal.gql('WHERE aws_key = :1', client_aws_key).get()
        if not self.requestor:
            self.error_invalid_access_key(client_aws_key)
            return False
            
     
     
        method = self.request.method
        headers = self.request.headers
        
        server_canonical_string = self.canonical_string(method=method, headers=headers, bucket=bucket, key=key, query_args = query_args)
        
        server_auth = "AWS %s:%s" % (self.requestor.aws_key, self.encode(self.requestor.aws_secret, server_canonical_string))
        
        
        logging.debug('server canonical: ' + server_canonical_string)
        logging.debug('server computed: ' + server_auth)
        logging.debug('client computed: ' + client_auth)
        
        if server_auth != client_auth:
            self.error_invalid_signature(client_aws_secrethash,self.requestor.aws_key,server_canonical_string)
            return False
        
    
        return True


    def add_key_query_filters(self, q, key):
        q.filter('name1 =', key[0:500])
        q.filter('name2 =', key[500:1000])
        q.filter('name3 =', key[1000:1500])
        return q

    def delete_object_if_exists(self, b, key):
        existing_oi = self.add_key_query_filters(ObjectInfo.all().ancestor(b),key).get()
        if existing_oi:
            existing_oc = ObjectContents.gql("WHERE ANCESTOR IS :1 LIMIT 1", existing_oi).get()
            if existing_oc:
                existing_oc.delete()
            existing_oi.acl.delete()
            existing_oi.delete()
            return existing_oi

    def object_metadata_as_response_headers(self, object_info):
        self.response.headers['Content-Length'] = str(object_info.size)  # this doesn't seem to work for head requests
        self.response.headers['ETag'] = str(object_info.etag)
        self.response.headers['Last-Modified'] = date_format_2(object_info.last_modified)
 
        for h in object_info.dynamic_properties():
            if h.lower().startswith('x-amz-meta-') or h.lower() in ['content-type','cache-control','content-disposition','expires','content-encoding']:
                value = getattr(object_info,h)
                if h.lower() == 'content-disposition':
                    h = 'Content-Disposition'
                if h.lower() == 'content-encoding':
                    h = 'Content-Encoding'
                self.response.headers[h] = str(value)



    def is_development_server(self):
        return self.request.environ.get('SERVER_SOFTWARE') == 'Development/1.0'


    def check_permission(self, acl, permission):
        if permission in ['READ_ACP','WRITE_ACP'] and acl.owner.id == self.requestor.id:
            return True
        for grant in acl.grants:
            if grant.grantee.id == self.requestor.id and grant.permission in [permission,'FULL_CONTROL']:
                return True
        self.error_access_denied()
        return False
    







    # error responses

    def error_entity_too_large(self,entity_size,max_size):
        self.error_generic(400, 'EntityTooLarge', 'Your proposed upload exceeds the maximum allowed object size.',
                           {'MaximumSize':max_size,'EntitySize':entity_size})
        
    def error_invalid_signature(self, sig, aws_key, string_to_sign):
        self.error_generic(403,'SignatureDoesNotMatch','The request signature we calculated does not match the signature you provided. Check your key and signing method.',
                           {'SignatureProvided':sig,
                            'StringToSignBytes':string_to_sign_bytes(string_to_sign),
                            'AWSAccessKeyId':aws_key,
                            'StringToSign':string_to_sign})
        
    def error_invalid_access_key(self, aws_key):
        self.error_generic(403,'InvalidAccessKeyId','The AWS Access Key Id you provided does not exist in our records.',{'AWSAccessKeyId':aws_key})

    def error_bucket_already_exists(self, bucket):
        self.error_generic(409,'BucketAlreadyExists','The requested bucket name is not available. The bucket namespace is shared by all users of the system. Please select a different name and try again.',{'BucketName':bucket})

    def error_bucket_not_empty(self, bucket):
        self.error_generic(409,'BucketNotEmpty','The bucket you tried to delete is not empty',{'BucketName':bucket})
 
    
    def error_no_such_key(self, key):
        self.error_generic(404,'NoSuchKey','The specified key does not exist',{'Key':key})

    def error_no_such_bucket(self, bucket):
        self.error_generic(404,'NoSuchBucket','The specified bucket does not exist',{'BucketName':bucket})

    def error_access_denied(self):
        self.error_generic(403,'AccessDenied','Access Denied')
        
    def error_key_too_long(self,max_size,size):
        self.error_generic(400,'KeyTooLongError','Your key is too long',{'MaxSizeAllowed':max_size,'Size':size})

    def error_invalid_argument_integer_range(self, arg_name, arg_value):
        self.error_invalid_argument(arg_name, arg_value, 'Argument %s must be an integer between 0 and 2147483647' % arg_name)
        
    def error_invalid_argument_not_integer(self, arg_name, arg_value):
        self.error_invalid_argument(arg_name, arg_value, 'Provided %s not an integer or within integer range' % arg_name)
  
    def error_invalid_argument(self, arg_name, arg_value, message):
        self.error_generic(400,'InvalidArgument',message,{'ArgumentName':arg_name, 'ArgumentValue':arg_value})

    def error_bad_digest(self, client, server):
        self.error_generic(400, 'BadDigest', 'The Content-MD5 you specified did not match what we received.', {'CalculatedDigest':server,'ExpectedDigest':client})

    def error_generic(self, status, code, message, fields={}):
        self.response.set_status(status)
        self.response.headers['Content-Type'] = 'application/xml'
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
        self.response.out.write( u'<Code>%s</Code>' % code)
        self.response.out.write( u'<Message>%s</Message>' % message)
        self.response.out.write( u'<RequestId>%s</RequestId>' % self.request_id)
        
        for field_name in fields:
            self.response.out.write( u'<%s>%s</%s>' % (field_name,str(fields[field_name]),field_name))
        
        self.response.out.write( u'<HostId>%s</HostId>' % self.host_id)
        self.response.out.write( u'</Error>')
        

