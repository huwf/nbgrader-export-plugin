"""
Tests to run on this plugin.

I'll steal some of the NBGrader utility functions for doing the testing.

We need to test:

1. Does the "read" return the expected value?
2. Does the "replace" replace the value as expected?
3. Does delete delete the value as expected?
4. Does the plugin handle failure as expected?
5. Do we check how many times the assignment can be submitted?
"""

import os
import shutil
from os.path import join
from nbgrader.utils import remove
from nbgrader.tests import run_nbgrader
from nbgrader.tests.apps.base import BaseTestApp

from unittest import mock
import pytest
from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint
from lti import ToolProvider, OutcomeRequest, OutcomeResponse


@pytest.fixture
def params():
    return {
        'lis_result_sourcedid': 'abcdef',
        'lis_outcome_service_url': 'http://www.example.com',
        'resource_link_id': '12345abcde',
        'user_id': 'foo',
        'oauth_consumer_key': 'key'
    }


from mock import MagicMock

@pytest.fixture
def validator():
    return RequestValidator()

@pytest.fixture
def authenticator(validator, monkeypatch):
    signature_authenticate = SignatureOnlyEndpoint(validator)
    monkeypatch.setattr(SignatureOnlyEndpoint, 'validate_request', True)
    return signature_authenticate

@pytest.fixture
def outcome_response_object():
    out = OutcomeResponse()
    out.score = 0.5

    return out


@pytest.fixture
def tool_provider_object(params, outcome_response_object, monkeypatch):

    tp = ToolProvider('key', 'secret', params)
    monkeypatch.setattr(ToolProvider, 'last_outcome_success', True)
    monkeypatch.setattr(ToolProvider, 'post_read_result', outcome_response_object)
    return tp


class TestNbGraderExportPlugin(BaseTestApp):

    def setup(self, course_dir, db):
        print('Running setup')
        with open("nbgrader_config.py", "a") as fh:
            fh.write("""c.NbGrader.db_assignments = [
                dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST'),
                dict(name='ps2', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
            fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")

        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps2", "p1.ipynb"))
        run_nbgrader(["assign", "ps1", "--db", db])
        run_nbgrader(["assign", "ps2", "--db", db])

        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
        self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps2", "p1.ipynb"))
        run_nbgrader(["autograde", "ps1", "--db", db])
        run_nbgrader(["autograde", "ps2", "--db", db])

    def test_assert_1_1(self):
        print("asserting")
        assert 0 == 1
    # def test_export(self, db, course_dir):
    #     self.setup(db, course_dir)
    #     run_nbgrader(["export", "--db", db])
    #     assert os.path.isfile("grades.csv")
    #     with open("grades.csv", "r") as fh:
    #         contents = fh.readlines()
    #         import shutil
    #         shutil.copy('grades.csv', '/home/huw/jupyter/nbgrader-fork/grades.csv.bak')
    #     assert len(contents) == 5
    #
    #     run_nbgrader(["export", "--db", db, "--to", "mygrades.csv"])
    #     assert os.path.isfile("mygrades.csv")
    #
    #     remove("grades.csv")
    #     run_nbgrader(["export", "--db", db, "--exporter", "nbgrader.plugins.CsvExportPlugin"])
    #     assert os.path.isfile("grades.csv")
    #
    # """
    # Testing with the LTI export plugin
    # """
    #
    # def test_lti_export_no_output_file(self, db, course_dir, outcome_response_object, monkeypatch):
    #     with open("nbgrader_config.py", "a") as fh:
    #         fh.write("""c.NbGrader.db_assignments = [
    #             dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST'),
    #             dict(name='ps2', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
    #         fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")
    #
    #     self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
    #     self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps2", "p1.ipynb"))
    #     run_nbgrader(["assign", "ps1", "--db", db])
    #     run_nbgrader(["assign", "ps2", "--db", db])
    #
    #     self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
    #     self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps2", "p1.ipynb"))
    #     run_nbgrader(["autograde", "ps1", "--db", db])
    #     run_nbgrader(["autograde", "ps2", "--db", db])
    #
    #     # Test that file does not exist if we specify it, but otherwise does.
    #     run_nbgrader(["export", "--db", db, "--exporter", "nbgrader.plugins.LtiExportPlugin",
    #                   "--key", "key", "--secret", "secret", "--user_id", "foo", "--assignment", "ps2"
    #                  ])
    #     assert not os.path.isfile("lti.xml")
    #
    # def test_lti_export(self, db, course_dir):
    #     with open("nbgrader_config.py", "a") as fh:
    #         fh.write("""c.NbGrader.db_assignments = [
    #             dict(name='ps1', duedate='2015-02-02 14:58:23.948203 PST'),
    #             dict(name='ps2', duedate='2015-02-02 14:58:23.948203 PST')]\n""")
    #         fh.write("""c.NbGrader.db_students = [dict(id="foo"), dict(id="bar")]""")
    #
    #     self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps1", "p1.ipynb"))
    #     self._copy_file(join("files", "submitted-unchanged.ipynb"), join(course_dir, "source", "ps2", "p1.ipynb"))
    #     run_nbgrader(["assign", "ps1", "--db", db])
    #     run_nbgrader(["assign", "ps2", "--db", db])
    #
    #     self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "bar", "ps1", "p1.ipynb"))
    #     self._copy_file(join("files", "submitted-changed.ipynb"), join(course_dir, "submitted", "foo", "ps2", "p1.ipynb"))
    #     run_nbgrader(["autograde", "ps1", "--db", db])
    #     run_nbgrader(["autograde", "ps2", "--db", db])
    #
    #
    #     run_nbgrader(["export", "--db", db, "--exporter", "nbgrader.plugins.LtiExportPlugin", "--to", "lti.xml",
    #                   "--key", "key", "--secret", "secret", "--user_id", "foo", "--assignment", "ps2"
    #                  ])
    #     assert os.path.isfile("lti.xml")

        # remove("lti.xml")



