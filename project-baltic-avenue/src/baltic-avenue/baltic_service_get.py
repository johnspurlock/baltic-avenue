from datetime import tzinfo, timedelta, datetime
import logging
from baltic_common import S3Operation
from baltic_model import *
from baltic_utils import *

class GetServiceOperation(S3Operation):

    def go(self):
        logging.info('GET service')
        
        if not self.check_auth():
            return
        

        self.response.set_status(200)
    
        self.response.headers['Content-Type'] = 'application/xml'
        
        
        #owner = Principal(id=private_info.id,display_name=private_info.display_name)
        
        #buckets = [
        #           Bucket(name='asdf2',creation_date=datetime(2007, 1, 15,19, 40, 34, 0, utc))
        #           ,Bucket(name='asdf3',creation_date=datetime(2007, 1, 15,19, 40, 34, 0, utc))
        #           ]
        
        
        buckets = [b for b in Bucket.all() if b.owner.id == self.requestor.id]
        
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
        
    
        self.response.out.write( u'<Owner><ID>%s</ID><DisplayName>%s</DisplayName></Owner>' % (self.requestor.id, self.requestor.display_name))
        self.response.out.write( u'<Buckets>')
        
        for b in buckets:
            self.response.out.write( u'<Bucket><Name>%s</Name><CreationDate>%s</CreationDate></Bucket>' % (b.name1 ,http_date(b.creation_date) ))
        
        
        self.response.out.write( u'</Buckets></ListAllMyBucketsResult>')
