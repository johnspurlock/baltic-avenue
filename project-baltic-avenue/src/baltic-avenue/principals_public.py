
from baltic_model import *

all_users = GroupPrincipal(
    id='65a011a29cdf8ec533ec3d1ccaae921c',
    display_name='AllUsers',
    uri='http://acs.amazonaws.com/groups/global/AllUsers')

s3_log_service = GroupPrincipal(
    id='3272ee65a908a7677109fedda345db8d9554ba26398b2ca10581de88777e2b61',
    display_name='s3-log-service',
    uri='http://acs.amazonaws.com/groups/s3/LogDelivery')


# To add custom users to your instance, add them here (as shown below) or in a new file named principals_private.py
# Persist to datastore using the 'update principals' action on the /admin page if on the dev server 
#   (auto-persisted once on startup if on the production server)

#your_user = UserPrincipal(
#    id='<user guid>',
#    display_name='<user display name>',
#    aws_key='<user access key>',
#    aws_secret='<user secret key>')
