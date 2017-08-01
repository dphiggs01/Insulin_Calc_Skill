import logging
import json
from tests.test_alexa_skill_base import TestAlexaSkillBase
from ask_amy.core.skill_factory import SkillFactory
import warnings

logger = logging.getLogger()

class DiabetesTest(TestAlexaSkillBase):


    def setUp(self):
        BASE_DIR=".."
        CONFIG=BASE_DIR+"/skill_config.json"
        self.dialog = SkillFactory.build(CONFIG)
        #boto3 does not close resources waits for gc cleanup
        warnings.filterwarnings("ignore", category=ResourceWarning)
        #self.dynamo_db = DynamoDB("Bolus", "http://localhost:8000")

    def test_reset_stored_values(self):
        self.logger.debug("DiabetesTest.test_reset_stored_values")
        # To Alexa: ask insulin calculator please reset the stored values
        request_dict, response_dict = self.get_request_response('test_reset_stored_values.json')
        dialog_response = self.dialog.begin(request_dict)
        self.assertEqual("OK I have reset the stored values in the insulin calculator.",
                          dialog_response['response']['outputSpeech']['text'])

    def test_open_insulin_calculator(self):
        self.logger.debug("DiabetesTest.test_open_insulin_calculator")
        # To Alexa: open insulin calculator
        request_dict, response_dict = self.get_request_response('test_open.json')
        dialog_response = self.dialog.begin(request_dict)
        speech = dialog_response['response']['outputSpeech']['ssml'][:49]
        self.assertEqual("<speak><p>Welcome to the insulin dose calculator.",
                               speech)

    def test_help_insulin_calculator(self):
        self.logger.debug("DiabetesTest.test_help_insulin_calculator")
        # To Alexa: ask insulin calculator for help
        request_dict, response_dict = self.get_request_response('test_help.json')
        dialog_response = self.dialog.begin(request_dict)
        speech = dialog_response['response']['outputSpeech']['ssml'][:48]
        self.assertEqual("<speak><p>The Insulin Calculator is intended for",
                         speech)

    def test_time_zone_request(self):
        self.logger.debug("DiabetesTest.test_time_zone_request")
        # To Alexa: ask insulin calculator What is my blood sugar correction dose?
        # Note: no time zone is set

        # Reset the DB
        request_dict, response_dict = self.get_request_response('test_reset_stored_values.json')
        self.dialog.begin(request_dict)

        #Expect a Time Zone Request
        request_dict, response_dict = self.get_request_response('test_time_zone_request.json')
        dialog_response = self.dialog.begin(request_dict)

        speech = dialog_response['response']['outputSpeech']['ssml'][:40]
        self.assertEqual("<speak><p>What time zone are you in?</p>",
                         speech)

    def test_blood_glucose_correction(self):
        self.logger.debug("DiabetesTest.test_blood_glucose_correction")
        # Alexa, ask Insulin Calculator What's my blood glucose correction dose?
        # Note: Required field already provided

        request_dict, response_dict = self.get_request_response('test_blood_glucose_correction.json')
        dialog_response = self.dialog.begin(request_dict)
        # logger.warning("REQUEST {}".format(json.dumps(dialog_response, sort_keys=True, indent=4)))
        speech = dialog_response['response']['outputSpeech']['text'][-43:]
        self.assertEqual("Your correction dose is 2 units of insulin.",
                         speech)

    def test_insulin_for_carbs(self):
        self.logger.debug("DiabetesTest.test_insulin_for_carbs")
        # Alexa, ask Insulin Calculator How many units of insulin do I need if I eat sixty grams of carbs?
        # Note: Required field already provided

        request_dict, response_dict = self.get_request_response('test_insulin_for_carbs.json')
        dialog_response = self.dialog.begin(request_dict)
        # logger.warning("REQUEST {}".format(json.dumps(dialog_response, sort_keys=True, indent=4)))
        speech = dialog_response['response']['outputSpeech']['text'][-31:]
        self.assertEqual("You need 10 units of insulin.  ",
                         speech)
