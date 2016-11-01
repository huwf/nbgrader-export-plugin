from nbgrader.plugins import ExportPlugin
from xml.etree import ElementTree as etree
from textwrap import dedent
import requests
import os
from traitlets import Unicode
from lti import ToolProvider
import lti


class LtiExportPlugin(ExportPlugin):
    """
    Exports the score for an individual student in LTI format.
    """
    # to = Unicode("", config=True, help="destination to export to.  If not specified, output is not written to file")
    user_id = Unicode("", config=True, help="The student we're enquiring about")
    assignment = Unicode("", config=True, help="The assignment we're enquiring about")
    sourced_id = Unicode(
        "",
        config=True,
        help=dedent(
            """
            For the LTI transfer, we need this value.  We don't need to know what it means.  It should come from
            the lis_result_sourcedid parameter in the initial LTI request.  Storage is left to the implementation.
            See: https://www.imsglobal.org/specs/ltiomv1p0/specification#toc-3
             """
        )
    )
    key = Unicode("", config=True, help="The client key for the OAUth request")
    secret = Unicode("", config=True, help="The client secret for the OAUth request")
    lis_outcome = Unicode(
        "",
        config=True,
        help="The URL of the LTI Outcomes service"
    )
    action = Unicode("read",
                     config=True,
                     help="The action to perform at the outcome service.  Options: read, replace, delete")

    def export(self, gradebook):

        student_score = gradebook.find_submission(self.assignment, self.user_id)
        lti_tool = ToolProvider(self.key, self.secret, params=self._generate_params(), launch_url=self.url)
        response = self.get_response(lti_tool, student_score)

        output_xml = response.generate_response_xml()
        response.process_xml(output_xml)
        # The score might be 0 so check for != None rather than falsy
        if response.score != None:
            self.log.info("The score retrieved from the server was %s" % str(response.score))
        if self.to == "":
            self.log.info("No output file specified, so only exporting to the server")
        else:
            with open('%s' % self.to, 'w', encoding='utf-8') as fh:
                self.log.info("Writing the result of the call to %s" % self.to)
                fh.write(output_xml)
        if not lti_tool.last_outcome_success():
            self.log.error("The outcome for the LTI request was %s" % response.description)

    def _generate_params(self):
        """
        This transfers the parameters into a dict for creating the object to request the server
        :return: A dictionary of parameters
        """
        return {
            'lis_outcome_service_url': self.url,
            'lis_result_sourcedid': self.sourced_id,
            'resource_link_id': self.url,
            'user_id': self.user_id,
            'oauth_consumer_key': self.key
        }

    def get_response(self, lti_tool, student_score):

        response = None
        # TODO: Sort out response_dict
        if self.action == 'replace':
            response = lti_tool.post_replace_result(student_score)
        if self.action == 'read':

            response = lti_tool.post_read_result()#outcome_opts=self.response_dict)
        elif self.action == 'delete':
            response = lti_tool.post_delete_result()
        else:
            self.log.error("Unrecognised action.  Please choose from replace, read, or delete")

        return response

    def _get_xml(self, outcome_request):
        return outcome_request.generate_request_xml()
