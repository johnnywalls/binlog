import pytest

from binlog.model import Model


def test_event_is_acked(tmpdir):
    with Model.open(tmpdir) as db:
        entry = db.create(test='data')

        db.register_reader('myreader')
        with db.reader('myreader') as reader:
            e = reader[0]
            assert e.pk not in reader.registry
            reader.ack(reader[0])
            assert e.pk in reader.registry


def test_acked_event_persist_after_reader_is_closed(tmpdir):
    with Model.open(tmpdir) as db:
        entry = db.create(test='data')

        db.register_reader('myreader')
        with db.reader('myreader') as reader:
            e = reader[0]
            reader.ack(e)

        # Reader commits registry on exit

        with db.reader('myreader') as reader:
            assert e.pk in reader.registry


def test_ack_on_unsaved_event(tmpdir):
    with Model.open(tmpdir) as db:
        db.register_reader('myreader')
        with db.reader('myreader') as reader:
            with pytest.raises(ValueError):
                reader.ack(Model(test='data'))


def test_ack_on_anonymous_reader(tmpdir):
    with Model.open(tmpdir) as db:
        entry = db.create(test='data')

        with db.reader() as reader:
            with pytest.raises(RuntimeError):
                reader.ack(reader[0])


def test_can_ack_with_pk(tmpdir):
    with Model.open(tmpdir) as db:
        entry = db.create(test='data')

        db.register_reader('myreader')
        with db.reader('myreader') as reader:
            reader.ack(0)
            assert 0 in reader.registry


def test_dont_accept_other_types(tmpdir):
    with Model.open(tmpdir) as db:
        db.register_reader('myreader')
        with db.reader('myreader') as reader:
            with pytest.raises(TypeError):
                reader.ack({})
