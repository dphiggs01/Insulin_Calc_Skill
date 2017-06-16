import unittest
import logging
import json
import os

class TestAlexaSkillBase(unittest.TestCase):
    """ Base class for Testing Alexa Skills
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Create and environment variable ASK_AMY_LOGGING to specify a logging directory
    path = os.getenv('ASK_AMY_LOGGING_DIR', os.path.expanduser('~')) + os.sep
    hdlr = logging.FileHandler(path + 'logfile.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)

    dialog = None  # dialog must be assigned in setup of the test

    # Helper functions
    def get_request_response(self, file_name):
        file_ptr_r = open("./data/{}".format(file_name), 'r')
        request_response = json.load(file_ptr_r)
        file_ptr_r.close()
        request = request_response['request']
        response = request_response['response']
        return request, response

    def request_response(self, file_name):
        request_dict, response_dict = self.get_request_response(file_name)
        dialog_response = self.dialog.begin(request_dict)
        if response_dict != {}:
            try:
                self.assertEquals(response_dict, dialog_response)
            except AssertionError:
                print("expected={}".format(json.dumps(response_dict, indent=4)))
                print("actual={}".format(json.dumps(dialog_response, indent=4)))
                raise AssertionError
        else:
            msg = "Warning: No assert in test as test {} data is empty!!".format(file_name)
            print("actual={}".format(dialog_response))
            print(msg)
            logging.debug(msg)
