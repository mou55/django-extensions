"""
JSONField automatically serializes most Python terms to JSON data.
Creates a TEXT field with a default value of "{}".  See test_json.py for
more information.

 from django.db import models
 from django_extensions.db.fields import json

 class LOL(models.Model):
     extra = json.JSONField()
"""
from __future__ import absolute_import
import six
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

try:
    # Django >= 1.7
    import json
except ImportError:
    # Django <= 1.6 backwards compatibility
    from django.utils import simplejson as json


def dumps(value):
    return DjangoJSONEncoder().encode(value)


def loads(txt):
    value = json.loads(
        txt,
        parse_float=Decimal,
        encoding=settings.DEFAULT_CHARSET
    )
    return value


class JSONDict(dict):
    """
    Hack so repr() called by dumpdata will output JSON instead of
    Python formatted data.  This way fixtures will work!
    """
    def __repr__(self):
        return dumps(self)


class JSONList(list):
    """
    As above
    """
    def __repr__(self):
        return dumps(self)


class JSONField(six.with_metaclass(models.SubfieldBase, models.TextField)):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.  Main thingy must be a dict object."""

    def __init__(self, *args, **kwargs):
        default = kwargs.get('default', None)
        if default is None:
            kwargs['default'] = '{}'
        elif isinstance(default, (list, dict)):
            kwargs['default'] = dumps(default)
        models.TextField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value is None or value == '':
            return {}
        elif isinstance(value, six.string_types):
            res = loads(value)
            if isinstance(res, dict):
                return JSONDict(**res)
            else:
                return JSONList(res)

        else:
            return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""
        if not isinstance(value, (list, dict)):
            return super(JSONField, self).get_db_prep_save("", connection=connection)
        else:
            return super(JSONField, self).get_db_prep_save(dumps(value),
                                                           connection=connection)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)
