import fastavro

import pytest

from decimal import Decimal
from io import BytesIO
from uuid import uuid4
import datetime


schema = {
    "fields": [
        {
            "name": "date",
            "type": {'type': 'int', 'logicalType': 'date'}
        },
        {
            "name": "timestamp-millis",
            "type": {'type': 'long', 'logicalType': 'timestamp-millis'}
        },
        {
            "name": "timestamp-micros",
            "type": {'type': 'long', 'logicalType': 'timestamp-micros'}
        },
        {
            "name": "uuid",
            "type": {'type': 'string', 'logicalType': 'uuid'}
        },
        {
            "name": "time-millis",
            "type": {'type': 'int', 'logicalType': 'time-millis'}
        },
        {
            "name": "time-micros",
            "type": {'type': 'long', 'logicalType': 'time-micros'}
        }
    ],
    "namespace": "namespace",
    "name": "name",
    "type": "record"
}


def serialize(schema, data):
    bytes_writer = BytesIO()
    fastavro.schemaless_writer(bytes_writer, schema, data)
    return bytes_writer.getvalue()


def deserialize(schema, binary):
    bytes_writer = BytesIO()
    bytes_writer.write(binary)
    bytes_writer.seek(0)

    res = fastavro.schemaless_reader(bytes_writer, schema)
    return res


def test_logical_types():
    data1 = {
        'date': datetime.date.today(),
        'timestamp-millis': datetime.datetime.now(),
        'timestamp-micros': datetime.datetime.now(),
        'uuid': uuid4(),
        'time-millis': datetime.datetime.now().time(),
        'time-micros': datetime.datetime.now().time(),

    }
    binary = serialize(schema, data1)
    data2 = deserialize(schema, binary)
    assert (data1['date'] == data2['date'])
    assert (data1['timestamp-micros'] == data2['timestamp-micros'])
    assert (int(data1['timestamp-millis'].microsecond / 1000) * 1000
            == data2['timestamp-millis'].microsecond)
    assert (int(data1['time-millis'].microsecond / 1000) * 1000
            == data2['time-millis'].microsecond)


def test_not_logical_ints():
    data1 = {
        'date': 1,
        'timestamp-millis': 2,
        'timestamp-micros': 3,
        'uuid': uuid4(),
        'time-millis': 4,
        'time-micros': 5,

    }
    binary = serialize(schema, data1)
    data2 = deserialize(schema, binary)
    # 1 day since 1970-1-1
    assert (data2['date'] == datetime.date(1970, 1, 2))


schema_null = {
    "fields": [
        {
            "name": "date",
            "type": ["null", {'type': 'int', 'logicalType': 'date'}]
        },
    ],
    "namespace": "namespace",
    "name": "name",
    "type": "record"
}


def test_null():
    data1 = {
        # 'date': None,
    }
    binary = serialize(schema_null, data1)
    data2 = deserialize(schema_null, binary)
    assert (data2['date'] is None)


schema_top = {
    "name": "n",
    "namespace": "namespace",
    "type": "bytes",
    "logicalType": "decimal",
    "precision": 15,
    "scale": 3,
}


def test_top():
    data1 = Decimal("123.456")
    binary = serialize(schema_top, data1)

    data2 = deserialize(schema_top, binary)
    assert (data1 == data2)


def test_negative():
    data1 = Decimal("-2.90")
    binary = serialize(schema_top, data1)
    data2 = deserialize(schema_top, binary)
    assert (data1 == data2)


def test_zero():
    data1 = Decimal("0.0")
    binary = serialize(schema_top, data1)
    data2 = deserialize(schema_top, binary)
    assert (data1 == data2)


def test_bytes_decimal():
    data1 = Decimal("123.456")
    binary = serialize(schema_top, data1)
    data2 = deserialize(schema_top, binary)
    assert (data1 == data2)


schema_leftmost = {
    "name": "n",
    "namespace": "namespace",
    "type": "bytes",
    "logicalType": "decimal",
    "precision": 18,
    "scale": 6,
}


def test_leftmost():
    binary = serialize(schema_leftmost, b'\xd5F\x80')
    data2 = deserialize(schema_leftmost, binary)
    assert (Decimal("-2.80") == data2)


def test_scale():
    data1 = Decimal("123.456678")  # does not fit scale
    with pytest.raises(AssertionError):
        serialize(schema_top, data1)
