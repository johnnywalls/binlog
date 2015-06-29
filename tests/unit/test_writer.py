from tempfile import mktemp
from unittest.mock import patch
import os
import shutil

from bsddb3.db import DBEnv, DB
import pytest

from binlog import writer


#
# Writer
#
def test_Writer_exists():
    """The Writer exists."""
    assert hasattr(writer, 'Writer')


#
# Writer()
#
def test_Writer_instantiation():
    """
    At the moment of instantiation the environment and the logindex
    must be created.
    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir)
        assert os.path.isdir(tmpdir)
        assert os.path.isfile(os.path.join(tmpdir, writer.LOGINDEX_NAME))
        assert isinstance(w.env, DBEnv().__class__)
        assert isinstance(w.logindex, DB().__class__)
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


#
# Writer().set_current_log
#
def test_Writer_set_current_log():
    """The Writer has the open_environ method."""
    assert hasattr(writer.Writer, 'set_current_log')


def test_Writer_set_current_log_on_new_environ():
    """
    When a new environ/logindex is created, set_current_log must create a
    new log and this new log must be registered in the logindex.
    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir)
        cl = w.set_current_log()

        assert os.path.isfile(os.path.join(tmpdir, writer.LOG_PREFIX + '.1'))
        assert isinstance(cl, DB().__class__)

        cursor = w.logindex.cursor()
        f_idx, f_name = cursor.first()
        l_idx, l_name = cursor.last()
        cursor.close()

        expected_idx = 1
        expected_name = (writer.LOG_PREFIX + '.1').encode('utf-8')

        assert f_idx == l_idx == expected_idx
        assert f_name == l_name ==  expected_name
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_set_current_log_on_created_but_is_empty():
    """
    If the environ is initialized, set_current_log must return the already
    created log if it have space available.
    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir)  # This will create the environ
        cl = w.set_current_log()         # This will create the first event DB
        del cl
        del w

        w = writer.Writer(tmpdir)
        cl = w.set_current_log()

        assert os.path.isfile(os.path.join(tmpdir, writer.LOG_PREFIX + '.1'))
        assert isinstance(cl, DB().__class__)

        cursor = w.logindex.cursor()
        f_idx, f_name = cursor.first()
        l_idx, l_name = cursor.last()
        cursor.close()

        expected_idx = 1
        expected_name = (writer.LOG_PREFIX + '.1').encode('utf-8')

        assert f_idx == l_idx == expected_idx
        assert f_name == l_name ==  expected_name
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_set_current_log_on_created_with_space():
    """
    If there is available space in the last log this must be returned.
    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir, max_log_events=10)  # This will create the environ
        cl = w.set_current_log()         # This will create the first event DB

        for i in range(5):
            cl.append(b'data')
        cl.close()
        del cl
        del w

        w = writer.Writer(tmpdir, max_log_events=10)
        cl = w.set_current_log()

        assert os.path.isfile(os.path.join(tmpdir, writer.LOG_PREFIX + '.1'))
        assert isinstance(cl, DB().__class__)

        cursor = w.logindex.cursor()
        f_idx, f_name = cursor.first()
        l_idx, l_name = cursor.last()
        cursor.close()

        expected_idx = 1
        expected_name = (writer.LOG_PREFIX + '.1').encode('utf-8')

        assert f_idx == l_idx == expected_idx
        assert f_name == l_name ==  expected_name
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_set_current_log_on_created_but_full():
    """
    If there is available space in the last log this must be returned.
    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir, max_log_events=10)  # This will create
                                                      # the environ
        cl = w.set_current_log()         # This will create the first event DB

        for i in range(10):
            cl.append(b'data')
        cl.close()
        del cl
        del w

        w = writer.Writer(tmpdir, max_log_events=10)
        cl = w.set_current_log()

        assert os.path.isfile(os.path.join(tmpdir, writer.LOG_PREFIX + '.2'))
        assert isinstance(cl, DB().__class__)

        cursor = w.logindex.cursor()
        f_idx, f_name = cursor.first()
        l_idx, l_name = cursor.last()
        cursor.close()

        expected_idx = 2
        expected_name = (writer.LOG_PREFIX + '.2').encode('utf-8')

        assert f_idx != l_idx == expected_idx
        assert f_name != l_name ==  expected_name
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)

#
# Writer().append
#
def test_Writer_append():
    """The Writer has the append method."""
    assert hasattr(writer.Writer, 'append')


def test_Writer_append_add_data_to_set_current_log():
    """
    When append() is called the data passed is pickelized and stored in
    the current log.
    """
    import pickle
    try:
        tmpdir = mktemp()

        expected = ["Some data", "Other data"]

        w = writer.Writer(tmpdir)
        w.append(expected)

        cl = w.set_current_log()
        cursor = cl.cursor()
        idx, data = cursor.first()
        cursor.close()

        actual = pickle.loads(data)

        assert expected == actual

    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_multiple_appends_creates_multiple_log():
    """
    When append is called multiple times, if max_log_events is reached,
    then a new log DB must be created.
    """
    import pickle
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir, max_log_events=2)
        for i in range(20):
            w.append("TEST DATA")

        cursor = w.logindex.cursor()

        for i in range(1, 11):  # Assert we created 10 DBs
            idx, _ = cursor.next()
            assert idx == i

        assert cursor.next() is None  # And nothing more
        cursor.close()

    except:
        raise
    finally:
        shutil.rmtree(tmpdir)

#
# Writer.delete
#
def test_Writer_delete():
    """The Writer has the delete method."""
    assert hasattr(writer.Writer, 'delete')


def test_Writer_delete_unused_db():
    """The Writer.delete method can delete an unused database."""
    from binlog.constants import LOG_PREFIX
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir, max_log_events=1)

        w.append("TEST DATA")
        assert os.path.exists(os.path.join(tmpdir, LOG_PREFIX + '.1'))

        w.append("TEST DATA")
        assert os.path.exists(os.path.join(tmpdir, LOG_PREFIX + '.2'))

        w.delete(1)
        
        assert not os.path.exists(os.path.join(tmpdir, LOG_PREFIX + '.1'))
        assert os.path.exists(os.path.join(tmpdir, LOG_PREFIX + '.2'))

    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_cant_delete_first_db_when_used():
    """
    The Writer.delete method can't delete the first database when there
    is only one database.

    """
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir)

        w.append("TEST DATA")
        w.set_current_log().sync()

        with pytest.raises(ValueError):
            w.delete(1)
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


def test_Writer_cant_delete_current():
    """
    The Writer.delete method can't delete the current database.

    """
    from binlog.constants import LOG_PREFIX
    try:
        tmpdir = mktemp()

        w = writer.Writer(tmpdir, max_log_events=2)

        for i in range(1, 11): 
            w.append("TEST DATA")
            w.set_current_log().sync()

            with pytest.raises(ValueError):
                w.delete(i)

            w.append("TEST DATA")
            w.set_current_log().sync()

            if i > 1:
                w.delete(i-1)
                assert not os.path.exists(
                    os.path.join(tmpdir, LOG_PREFIX + '.' + str(i-1)))
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)


@pytest.mark.parametrize("num_reads", range(1, 21))
def test_delete_and_read(num_reads):
    from binlog.reader import Reader
    from binlog.writer import Writer
    MAX_LOG_EVENTS = 10
    try:
        tmpdir = mktemp()

        writer = Writer(tmpdir, max_log_events=MAX_LOG_EVENTS)
        reader = Reader(tmpdir, checkpoint='test')

        for x in range(25):
            writer.append(x)

        for x in range(num_reads):
            reader.next_record()

        if num_reads > MAX_LOG_EVENTS:
            writer.delete(1)
        else:
            with pytest.raises(ValueError):
                writer.delete(1)
    except:
        raise
    finally:
        shutil.rmtree(tmpdir)

