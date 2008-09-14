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
        
        
        # public user
        if self.requestor == self.all_users:
            logging.info('self.requestor == self.all_users')
            # s3 will actually 307 redirect to  aws.amazon.com/s3,
            # but we'll simply return 403 access denied
            self.error_access_denied()
            return
        


        # authenticated user, we're ok, list the buckets they own
        self.response.set_status(200)
    
        self.response.headers['Content-Type'] = 'application/xml'
        
        buckets = [b for b in Bucket.all() if b.owner.id == self.requestor.id]
        
        self.response.out.write( u'<?xml version="1.0" encoding="UTF-8"?>\n<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">')
        self.response.out.write( u'<Owner><ID>%s</ID><DisplayName>%s</DisplayName></Owner>' % (self.requestor.id, self.requestor.display_name))
        self.response.out.write( u'<Buckets>')
        for b in buckets:
            self.response.out.write( u'<Bucket><Name>%s</Name><CreationDate>%s</CreationDate></Bucket>' % (b.name1 ,date_format_1(b.creation_date) ))
        self.response.out.write( u'</Buckets></ListAllMyBucketsResult>')
