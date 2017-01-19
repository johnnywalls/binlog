import pytest

from binlog.database import Config
from binlog.database import Entries
from binlog.database import Checkpoints
from binlog.serializer import NumericSerializer
from binlog.serializer import ObjectSerializer
from binlog.serializer import TextSerializer


@pytest.mark.parametrize(
    "database,key_serializer,value_serializer",
    [(Checkpoints, TextSerializer, ObjectSerializer),
     (Config, TextSerializer, ObjectSerializer),
     (Entries, NumericSerializer, ObjectSerializer)])
def test_database_serializers(database, key_serializer, value_serializer):
    assert database.K is key_serializer
    assert database.V is value_serializer

