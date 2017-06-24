import logging
import datetime
from ask_amy.core.default_dialog import DefaultDialog
from ask_amy.core.reply import Reply, Response, Card, Prompt

from ask_amy.utilities.time_of_day import TimeOfDay

logger = logging.getLogger()


class DiabetesDialog(DefaultDialog):

    def launch_request(self, method_name=None):
        logger.debug("**************** entering DiabetesDialog.launch_request")
        return self.execute_method('welcome_request')


    def blood_glucose_correction(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        self.event.slot_data_to_session_attributes()

        # 3. See if we have all the data we need
        required_fields = ['terms_of_use', 'time_adj', 'current_bg_level', 'target_bg_level_' + self.day_night_prefix(),
                           'correction_factor_' + self.day_night_prefix()]

        reply_dict = self.required_fields_process(required_fields)
        if reply_dict is not None:
            return reply_dict

        # 5. Give result when we have all the data
        correction = self.calc_blood_glucose_correction()
        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.session.save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.session)

    def calc_blood_glucose_correction(self):
        current_bg_level = self.session.get_attribute(['current_bg_level'])
        target_bg_level = self.session.get_attribute(['target_bg_level_' + self.day_night_prefix()])
        correction_factor = self.session.get_attribute(['correction_factor_' + self.day_night_prefix()])
        correction = int(round((float(current_bg_level) - float(target_bg_level)) / float(correction_factor), 0))
        time_adj = self.session.get_attribute(['time_adj'])
        self.session.put_attribute("current_time", TimeOfDay.current_time(time_adj))
        self.session.put_attribute("day_night", self.day_night_prefix())
        self.session.put_attribute("target_bg_level", target_bg_level)
        self.session.put_attribute("correction_factor", correction_factor)
        self.session.put_attribute("correction", correction)
        return correction

    def insulin_for_carb_consumption(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        self.event.slot_data_to_session_attributes()

        # 3. See if we have all the data we need
        required_fields = ['terms_of_use', 'time_adj', 'amt_of_carbs', 'carb_ratio_' + self.mealtime_prefix()]
        reply_dict = self.required_fields_process(required_fields)
        if reply_dict is not None:
            return reply_dict

        # 5. Give result
        correction = self.calc_insulin_for_carb_consumption()
        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.session.save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.session)

    def calc_insulin_for_carb_consumption(self):
        amt_of_carbs = self.session.get_attribute(['amt_of_carbs'])
        carb_ratio = self.session.get_attribute(['carb_ratio_' + self.mealtime_prefix()])
        correction = int(round(float(amt_of_carbs) / float(carb_ratio), 0))
        self.session.put_attribute("mealtime", self.mealtime_prefix())
        self.session.put_attribute("carb_ratio", carb_ratio)
        self.session.put_attribute("correction", correction)
        return correction

    def bg_correction_with_carbs(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        self._event.slot_data_to_session_attributes()

        required_fields = ['terms_of_use', 'time_adj', 'amt_of_carbs', 'current_bg_level',
                           'target_bg_level_' + self.day_night_prefix(),
                           'correction_factor_' + self.day_night_prefix(), 'carb_ratio_' + self.mealtime_prefix()]

        reply_dict = self.required_fields_process(required_fields)
        if reply_dict is not None:
            return reply_dict

        # 5. Give result when we have all the data
        bg_correction = self.calc_blood_glucose_correction()
        carb_correction = self.calc_insulin_for_carb_consumption()

        correction = carb_correction
        if bg_correction > 0:
            correction += bg_correction
        self.session.put_attribute("correction", correction)

        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.session.save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.session)

    def requested_value_intent(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != method_name:
            return self.handle_session_end_confused()
        else:
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)

    def agree_to_terms(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))

        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != method_name:
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        requested_value = self.request.value_for_slot_name('terms_of_use')

        # 3. See if we have all the data we need
        # 4. Request data if needed
        if requested_value is None:
            reply_intent_dict = intent_dict['conditions']['listen']
            return Reply.build(reply_intent_dict, self.session)

        if requested_value == "agree":
            logger.debug('AGREED to AGREEMENT')
            date_str = datetime.date.today().strftime("%B %d, %Y")
            self.session.put_attribute('terms_of_use', date_str)
            self.session.save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        elif requested_value == "disagree":
            reply_intent_dict = intent_dict['conditions']['disagree']
        else:
            # We got a value in the slot but it is neither agree or disagree
            reply_intent_dict = intent_dict['conditions']['retry']

        return Reply.build(reply_intent_dict, self.session)

    def set_current_time(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != method_name:
            return self.handle_session_end_confused()

        requested_value = self.request.value_for_slot_name('time')
        time_am_pm = self.request.value_for_slot_name('ampm')
        time_adj = TimeOfDay.time_adj(requested_value, time_am_pm)

        logger.debug(" time={} time_am_pm={} adj={}".format(requested_value, time_am_pm, time_adj))
        if time_adj is not None:
            self.session.put_attribute('time_adj', str(time_adj))
            self.session.save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        else:
            intent_dict = self.get_intent_details(method_name)
            return Reply.build(intent_dict['conditions']['retry'], self.session)

    def welcome_request(self, method_name=None):
        """ Play welcome message and wait for a response
        """
        return self.handle_default_intent(method_name)

    def help_request(self, method_name=None):
        """ Reset any establish conversation and play help message
        """
        self.reset_established_dialog()
        return self.handle_default_intent(method_name)

    def reset_stored_values(self, method_name=None):
        self.session.reset_stored_values()
        return self.handle_default_intent(method_name)

    def handle_session_end_request(self, method_name=None):
        return self.handle_default_intent(method_name)

    def handle_session_end_confused(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.handle_session_end_confused')
        logger.debug("session={}".format(self.session.attributes()))
        logger.debug("request={}".format(self.event.request))
        # can we re_prompt?
        retry_attempted = self.session.get_attribute(["retry_attempted"])
        if retry_attempted is None:
            prompt_dict = {"speech_out_text": "Could you please repeat or say help.",
                          "should_end_session": False}
            requested_value_nm = self.session.get_attribute(['requested_value_nm'])
            if requested_value_nm is not None:
                prompt_dict = self.get_re_prompt_for_slot_data(requested_value_nm)

            self.session.put_attribute("retry_attempted", True)
            return Reply.build(prompt_dict, self.session)
        else:
            # we are done
            return self.handle_default_intent(method_name='handle_session_end_confused')

    # --------------- Helper Methods

    def is_good_state(self, method_name):
        state_good = True
        established_dialog = self.peek_established_dialog()
        if established_dialog is not None:
            if established_dialog != method_name:
                state_good = False
        else:
            self.push_established_dialog(method_name)
        return state_good

    def required_fields_process(self, required_fields):
        reply_dict = None
        for key in required_fields:
            value = self.session.get_attribute([key])
            logger.debug("      key   {}".format(key))
            logger.debug("      value {}".format(value))

            # 4. Request data if needed
            if value is None:
                logger.debug("      none condition key={}".format(key))
                expected_intent = self.get_expected_intent_for_data(key)
                self.push_established_dialog(expected_intent)
                self.session.put_attribute('requested_value_nm', key)

                reply_slot_dict = self.get_slot_data_details(key)
                return Reply.build(reply_slot_dict, self.session)

        return reply_dict

    def day_night_prefix(self):
        time_adj = self.session.get_attribute(['time_adj'])
        prefix = 'night'
        if TimeOfDay.day_night(time_adj) == TimeOfDay.Daytime:
            prefix = 'day'
        return prefix

    def mealtime_prefix(self):
        time_adj = self.session.get_attribute(['time_adj'])
        if TimeOfDay.meal_time(time_adj) == TimeOfDay.Breakfast:
            prefix = 'breakfast'
        elif TimeOfDay.meal_time(time_adj) == TimeOfDay.Lunch:
            prefix = 'lunch'
        else:
            prefix = 'dinner'
        return prefix

    def execute_method(self, method_name):
        """ Execute a method in this class given its name
        """
        method = getattr(self, method_name)
        return method(method_name)
