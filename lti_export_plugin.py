from nbgrader.plugins import ExportPlugin
from xml.etree import ElementTree as etree
from textwrap import dedent
import requests
import os
from traitlets import Unicode
from lti import ToolProvider
import lti
import sys

class LtiExportPlugin(ExportPlugin):
    """
    Exports the score for an individual student in LTI format.
    """
    # to = Unicode("", config=True, help="destination to export to.  If not specified, output is not written to file")
    nbgrader_id = Unicode("", config=True, help="The student name according to NBGrader")
    user_id = Unicode("", config=True, help="The ID of the student in the LMS")
    assignment = Unicode("", config=True, help="The assignment we're enquiring about")
    lis_result_sourcedid = Unicode(
        "",
        config=True,
        help=dedent(
            """
            For the LTI transfer, we need this value.  We don't need to know what it means.  It should come from
            the lis_result_sourcedid parameter in the initial LTI request.  Storage is left to the implementation.
            See: https://www.imsglobal.org/specs/ltiomv1p0/specification#toc-2

            This parameter contains an identifier that indicates the LIS Result Identifier (if any) associated with
            this launch.  It identifies a unique row and column within the TC gradebook.  This identifier is unique for
            every combination of resource_link_id / user_id but its value may change from one launch to the next.
            The TP should only retain the most recent value for this field for a particular resource_link_id / user_id.
            This parameter is optional.
             """
        )
    )
    key = Unicode("", config=True, help="The client key for the OAUth request")
    secret = Unicode("", config=True, help="The client secret for the OAUth request")
    lis_outcome_service_url = Unicode(
        "",
        config=True,
        help=dedent(
            """
            The URL of the LTI Outcomes service.  See: https://www.imsglobal.org/specs/ltiomv1p0/specification#toc-3

            This parameter should be no more than 1023 characters long.   This value should not change from one launch
            to the next and in general, the TP can expect that there is a one-to-one mapping between the
            lis_outcome_service_url and a particular oauth_consumer_key.  This value might change if there was a
            significant re-configuration of the TC system or if the TC moved from one domain to another.  The TP can
            assume that this URL generally does not change from one launch to the next but should be able to deal with
            cases where this value rarely changes.   The service URL may support various operations / actions.  The
            Basic Outcomes Service Provider will respond with a response of 'unimplemented' for actions it does not
            support. This field is required if the TC is accepting outcomes for any launches associated with the
            resource_link_id.
            """
        )
    )
    action = Unicode("read",
                     config=True,
                     help="The action to perform at the outcome service.  Options: read, replace, delete")

    def export(self, gradebook):
        """

        :param gradebook:
        :return:
        """
        student_score = gradebook.find_submission(self.assignment, self.nbgrader_id).score
        self.log.info("student_score: %s" % student_score)
        lti_tool = ToolProvider(self.key, self.secret, params=self._generate_params(), launch_url=self.lis_outcome_service_url)
        response = self.get_response(lti_tool, student_score)

        output_xml = response.generate_response_xml()
        response.process_xml(output_xml)

        # The score might be 0 so check for != None rather than falsy
        if response.score != None:
            self.log.info("The score retrieved from the server was %s" % response.score)
        if self.to == "":
            self.log.info("No output file specified, so not writing to file.")
        else:
            with open('%s' % self.to, 'w', encoding='utf-8') as fh:
                self.log.info("Writing the result of the call to %s" % self.to)
                fh.write(output_xml)
        if not lti_tool.last_outcome_success():
            self.fail("The outcome for the LTI request was %s" % response.description)

    def _generate_params(self):
        """
        This transfers the parameters into a dict for creating the object to request the server
        :return: A dictionary of parameters
        """
        return {
            'lis_outcome_service_url': self.lis_outcome_service_url,
            'lis_result_sourcedid': self.lis_result_sourcedid,
            'oauth_consumer_key': self.key
        }

    def get_response(self, lti_tool, student_score):

        response = None
        # TODO: Sort out response_dict
        self.action = self.action.strip()

        self.log.info('self.action: %s' % self.action)
        if self.action == 'replace':
            response = lti_tool.post_replace_result(student_score)
        elif self.action == 'read':
            response = lti_tool.post_read_result()
        elif self.action == 'delete':
            response = lti_tool.post_delete_result()
        else:
            self.fail("Unrecognised action.  Please choose from replace, read, or delete")

        return response

    def _get_xml(self, outcome_request):
        return outcome_request.generate_request_xml()

    def fail(self, msg, *args):
        """Log the error msg using self.log.error and exit using sys.exit(1)."""
        self.log.error(msg, *args)
        sys.exit(1)
