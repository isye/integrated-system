import pytest, sqlalchemy

from integrated_api import postgres

@pytest.fixture
def test_get_pgcon(app):
    with app.app_context():
        con = postgres.get_pgcon()
        assert con is postgres.get_pgcon()

    with pytest.raises(sqlalchemy.ProgrammingError) as e:
        con.execute('SELECT 1')

