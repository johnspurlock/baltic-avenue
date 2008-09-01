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

        
    # generates the aws canonical string for the given parameters
    def canonical_string(self, method, bucket="", key=None, query_args={}, headers={}, expires=None):
        
        
        AMAZON_HEADER_PREFIX = 'x-amz-'
        
        interesting_headers = {}
        for header_key in headers:
            lk = header_key.lower()
            if lk in ['content-md5', 'content-type', 'date'] or lk.startswith(AMAZON_HEADER_PREFIX):
                interesting_headers[lk] = headers[header_key].strip()
    
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



        # add the key.  even if it doesn't exist, add the slash
        if key:
            buf += '/' + urllib.quote_plus(key)
            
        # handle special query string arguments
    
        if query_args.has_key("acl"):
            if not key:
                buf += '/'  # only add a trailing slash for acl???
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
        
        # check auth header present
        client_auth = self.request.headers.get('Authorization')
        if not client_auth:
            self.error_generic(400,'NoAuthHeader','Expecting an Authorization header')
            return False
        
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















    # error responses

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
        
    def error_generic(self, status, code, message, fields={}):
        self.response.set_status(status)
        self.response.headers['Content-Type'] = 'application/xml'
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<Error>')
        self.response.out.write( u'<Code>%s</Code>' % code)
        self.response.out.write( u'<Message>%s</Message>' % message)
        self.response.out.write( u'<RequestId>%s</RequestId>' % self.request_id)
        
        for field_name in fields:
            self.response.out.write( u'<%s>%s</%s>' % (field_name,fields[field_name],field_name))
        
        self.response.out.write( u'<HostId>%s</HostId>' % self.host_id)
        self.response.out.write( u'</Error>')
        

