import pytest
import ckanext.fulltext.commands.fulltext as cli
import ckanext.fulltext.jobs as jobs

TEST_QUEUE_NAME = "Test"


def fail_func():
    raise Exception('boom')

def clean_queue():
    jobs.requeue_all_failed(TEST_QUEUE_NAME)
    jobs.clear_all(TEST_QUEUE_NAME)

def test_list_errors_with_errors():
    
    jobs.add(fn=fail_func, title="TestException", queue=TEST_QUEUE_NAME)
    jobs.start_worker(TEST_QUEUE_NAME, burst=True)
    result = cli._list_errors(queue_name=TEST_QUEUE_NAME)[0]
    jobs.clear_all(TEST_QUEUE_NAME)
    assert 'Job with args' in result

def test_list_errors_without_errors():
    clean_queue()
    assert 'No failed jobs found.' == cli._list_errors(queue_name=TEST_QUEUE_NAME)


def test_empty_requeue_jobs():
    clean_queue()
    assert  "0" in cli._requeue_failed_jobs(queue_name=TEST_QUEUE_NAME)

def test_requeue_jobs():
    clean_queue()
    jobs.add(fn=fail_func, title="TestException", queue=TEST_QUEUE_NAME)
    jobs.start_worker(TEST_QUEUE_NAME, burst=True)
    result = cli._requeue_failed_jobs(queue_name=TEST_QUEUE_NAME)
    assert '1' in result

# def test_futur_init_table():
#     cli._init_fulltext_table("01.01.2050")

# def test_past_init_table():
#     cli._init_fulltext_table("01.01.2013")

# def test_none_init_table():
#     cli._init_fulltext_table(None)
