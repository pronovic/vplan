# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, patch

from vplan.engine.database import _AccountEntity, _PlanEntity, db_retrieve_all_tables, setup_database


class TestLifecycle:
    @patch("vplan.engine.database.config")
    def test_database_lifecycle(self, config, tmpdir):
        database_url = "sqlite+pysqlite:///%s" % tmpdir.join("vplan.sqlite").realpath()
        config.return_value = MagicMock(database_url=database_url)
        setup_database()
        assert db_retrieve_all_tables() == [
            _AccountEntity.__tablename__,
            _PlanEntity.__tablename__,
        ]
