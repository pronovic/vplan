# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:
from unittest.mock import MagicMock, patch

from vplan.engine.database import get_tables, setup_database
from vplan.engine.entity import AccountEntity, PlanEntity


class TestLifecycle:
    @patch("vplan.engine.database.config")
    def test_database_lifecycle(self, config, tmpdir):
        database_url = "sqlite+pysqlite:///%s" % tmpdir.join("vplan.sqlite").realpath()
        config.return_value = MagicMock(database_url=database_url)
        setup_database()
        assert get_tables() == [
            AccountEntity.__tablename__,
            PlanEntity.__tablename__,
        ]
