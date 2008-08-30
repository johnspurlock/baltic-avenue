

import re

from google.appengine.api import validation
from google.appengine.api import yaml_listener
from google.appengine.api import yaml_builder
from google.appengine.api import yaml_object


AWS_KEY_RE_STRING = r'(?!-)[a-zA-Z0-9\+]+' 
AWS_SECRET_RE_STRING = r'(?!-)[a-zA-Z0-9\+]+'
OWNER_ID_RE_STRING = r'(?!-)[a-zA-Z0-9\+]+'
OWNER_DISPLAY_NAME_RE_STRING = r'(?!-)[a-zA-Z0-9\+]+'


AWS_KEY = 'aws_key'
AWS_SECRET = 'aws_secret'
OWNER_ID = 'owner_id'
OWNER_DISPLAY_NAME = 'owner_display_name'



class PrivateInfoExternal(validation.Validated):
  """Class representing users application info.

  This class is passed to a yaml_object builder to provide the validation
  for the application information file format parser.

  Attributes:
    application: Unique identifier for application.
    version: Application's major version number.
    runtime: Runtime used by application.
    api_version: Which version of APIs to use.
    handlers: List of URL handlers.
    default_expiration: Default time delta to use for cache expiration for
      all static files, unless they have their own specific 'expiration' set.
      See the URLMap.expiration field's documentation for more information.
    skip_files: An re object.  Files that match this regular expression will
      not be uploaded by appcfg.py.  For example:
        skip_files: |
          .svn.*|
          #.*#
  """

  ATTRIBUTES = {

    AWS_KEY: AWS_KEY_RE_STRING,
    AWS_SECRET: AWS_SECRET_RE_STRING,
    OWNER_ID: OWNER_ID_RE_STRING,
    OWNER_DISPLAY_NAME: OWNER_DISPLAY_NAME_RE_STRING,

  }



def LoadSinglePrivateInfo(private_info):
  """Load a single PrivateInfo object where one and only one is expected.

  Args:
    app_info: A file-like object or string.  If it is a string, parse it as
    a configuration file.  If it is a file-like object, read in data and
    parse.

  Returns:
    An instance of AppInfoExternal as loaded from a YAML file.

  Raises:
    EmptyConfigurationFile when there are no documents in YAML file.
    MultipleConfigurationFile when there is more than one document in YAML
    file.
  """
  builder = yaml_object.ObjectBuilder(PrivateInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(private_info)

  app_infos = handler.GetResults()
  if len(app_infos) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(app_infos) > 1:
    raise appinfo_errors.MultipleConfigurationFile()
  return app_infos[0]

