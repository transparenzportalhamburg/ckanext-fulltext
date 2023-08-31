import pytest
from ckanext.fulltext.tests.server_mock import ServerMock, PORT

@pytest.fixture(scope="module")
def server():
    server = ServerMock(PORT)
    server.start()
    yield server
    server.close()
    server.join()
