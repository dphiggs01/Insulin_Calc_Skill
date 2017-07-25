import logging
import json
from tests.test_alexa_skill_base import TestAlexaSkillBase
from ask_amy.core.skill_factory import SkillFactory

logger = logging.getLogger()

class DiabetesTest(TestAlexaSkillBase):
    def setUp(self):
        BASE_DIR=".."
        CONFIG=BASE_DIR+"/skill_config.json"
        self.dialog = SkillFactory.build(CONFIG)
        #self.dynamo_db = DynamoDB("Bolus", "http://localhost:8000")

    def test_error(self):
        file_name = 'ERROR_TEST.json'
        file_ptr_r = open("./data/{}".format(file_name), 'r')
        request_dict = json.load(file_ptr_r)
        dialog_response = self.dialog.begin(request_dict)
        print(json.dumps(dialog_response, indent=4))


    def test_reset_stored_values(self):
        self.logger.debug("DiabetesTest.test_reset_stored_values")
        # To Alexa: ask insulin calculator please reset the stored values
        self.request_response('test_reset_stored_values.json')

    def test_open_insulin_calculator(self):
        self.logger.debug("DiabetesTest.test_open_insulin_calculator")
        # To Alexa: open insulin calculator
        self.request_response('test_open.json')

    def test_help_insulin_calculator(self):
        self.logger.debug("DiabetesTest.test_help_insulin_calculator")
        # To Alexa: help insulin calculator
        self.request_response('test_help.json')

    def test_glood_glucose_correction(self):
        self.logger.debug("DiabetesTest.test_glood_glucose_correction")
        # To Alexa: What is my blood sugar correction dose?
        self.request_response('test_blood_glucose_correction.json')

    def test_glood_glucose_correction_level(self):
        self.logger.debug("DiabetesTest.test_glood_glucose_correction_level")
        # From System: What is your current blood glucose level?
        # To Alexa: two hundred
        # FAILING BECAUSE THE TIME IS NOT MOCKED
        # self.request_response('test_blood_glucose_correction_level.json')

    def test_agreement_prompt(self):
        self.logger.debug("DiabetesTest.test_agreement_prompt")
        # To Alexa: What is my blood sugar correction dose?
        # Precondition No agreement set in session
        self.request_response('test_agreement_prompt.json')


    def test_agreement_terms(self):
        self.logger.debug("DiabetesTest.test_agreement_terms")
        # To Alexa: I would like to hear the terms
        # Precondition No agreement set in session
        self.request_response('test_agreement_terms.json')

    def test_set_time_prompt(self):
        self.logger.debug("DiabetesTest.test_set_time_prompt")
        # To Alexa: I would like to hear the terms
        # From system: What is the current time.
        # Precondition No time set in session
        self.request_response('test_set_time_prompt.json')

    def test_set_time_set_value(self):
        self.logger.debug("DiabetesTest.test_set_time_value")
        # To Alexa: I would like to hear the terms
        # From system: What is the current time.
        # Precondition No time set in session
        # FAILING BECAUSE THE TIME IS NOT MOCKED
        # self.request_response('test_set_time_value.json')


