
from google.appengine.ext import db

class Principal(db.Model):
    id = db.StringProperty(required=True)
    display_name = db.StringProperty(required=True)

class UserPrincipal(Principal):
    aws_key = db.StringProperty(required=True)
    aws_secret = db.StringProperty(required=True)
    email = db.EmailProperty()

class GroupPrincipal(Principal):
    uri = db.LinkProperty(required=True)

class ACL(db.Model):
    owner = db.ReferenceProperty(Principal,required=True)  #parent

class ACLGrant(db.Model):
    acl = db.ReferenceProperty(ACL,required=True)  #parent
    grantee = db.ReferenceProperty(Principal,required=True)
    permission = db.StringProperty(required=True,choices=['READ','WRITE','READ_ACP','WRITE_ACP','FULL_CONTROL'])

class Bucket(db.Model):
    owner = db.ReferenceProperty(Principal,required=True)
    name1 = db.StringProperty(required=True)
    creation_date = db.DateTimeProperty(required=True)
    acl = db.ReferenceProperty(ACL,required=True)
    
class ObjectInfo(db.Expando):
    bucket = db.ReferenceProperty(Bucket,required=True)  #parent
    name1 = db.StringProperty(required=True)
    name2 = db.StringProperty()
    name3 = db.StringProperty()    # keys can be at max 1024 bytes utf-8 encoded
    last_modified = db.DateTimeProperty(required=True)
    etag = db.StringProperty(required=True)
    size = db.IntegerProperty(required=True)  #aka content-length
    owner = db.ReferenceProperty(Principal,required=True)
    acl = db.ReferenceProperty(ACL,required=True)

    def full_name(self):
        return self.name1 +  self.name2 +  self.name3

class ObjectContents(db.Model):
    object_info = db.ReferenceProperty(ObjectInfo,required=True) #parent
    contents = db.BlobProperty()  # not required to support zero-byte files

class LogRecord(db.Model):
    bucket_owner = db.StringProperty(required=True) #principal.id
    bucket = db.StringProperty(required=True)  #bucket.name
    time = db.DateTimeProperty(required=True)
    remote_ip = db.StringProperty(required=True)
    requestor = db.StringProperty(required=True)  #principal.id
    request_id = db.StringProperty(required=True)
    operation = db.StringProperty(required=True) #choices??
    key_ = db.StringProperty(name="key")   #key.name
    request_uri = db.StringProperty(required=True) # GET /asdf?asdf HTTP 1.1
    http_status = db.IntegerProperty(required=True)
    error_code = db.StringProperty()
    bytes_sent = db.IntegerProperty(required=True)
    object_size = db.IntegerProperty(required=True)
    total_time_millis = db.IntegerProperty(required=True)
    turnaround_time_millis = db.IntegerProperty(required=True)
    referrer = db.StringProperty()
    user_agent = db.StringProperty(required=True)
    
    

