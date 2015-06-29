from tempfile import mktemp
import shutil

import pytest


def test_reader_starts_with_the_lowest_database_available():
    from binlog.reader import Reader
    from binlog.writer import Writer

    try:
        tmpdir = mktemp()

        writer = Writer(tmpdir, max_log_events=10)

        for x in range(25):
            writer.append(x)

        writer.delete(1)

        reader = Reader(tmpdir, checkpoint='test')
        for x in range(10, 25):
            rec = reader.next_record()
            print(rec)
            assert rec.value == x
        assert reader.next_record() is None
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_reader_starts_with_the_lowest_database_available_instantiate_before_delete():
    from binlog.reader import Reader
    from binlog.writer import Writer

    try:
        tmpdir = mktemp()

        writer = Writer(tmpdir, max_log_events=10)
        reader = Reader(tmpdir, checkpoint='test')

        for x in range(25):
            writer.append(x)

        writer.delete(1)

        for x in range(10, 25):
            rec = reader.next_record()
            print(rec)
            assert rec.value == x
        assert reader.next_record() is None
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)