import logging
import datetime
from ask_amy.default_dialog import DefaultDialog
from ask_amy.reply import Reply, Response, Card, Prompt

from ask_amy.time_of_day import TimeOfDay

logger = logging.getLogger()


class DiabetesDialog(DefaultDialog):
    def blood_glucose_correction(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        self.map_requested_value(from_initial_utterance='current_bg_level')

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

        self.event().session().save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.event().session())

    def calc_blood_glucose_correction(self):
        current_bg_level = self.event().get_value_in_session(['current_bg_level'])
        target_bg_level = self.event().get_value_in_session(['target_bg_level_' + self.day_night_prefix()])
        correction_factor = self.event().get_value_in_session(['correction_factor_' + self.day_night_prefix()])
        correction = int(round((float(current_bg_level) - float(target_bg_level)) / float(correction_factor), 0))
        time_adj = self.event().get_value_in_session(['time_adj'])
        self.event().set_value_in_session("current_time", TimeOfDay.current_time(time_adj))
        self.event().set_value_in_session("day_night", self.day_night_prefix())
        self.event().set_value_in_session("target_bg_level", target_bg_level)
        self.event().set_value_in_session("correction_factor", correction_factor)
        self.event().set_value_in_session("correction", correction)
        return correction

    def insulin_for_carb_consumption(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        self.map_requested_value(from_initial_utterance='carbs_being_eaten')

        # 3. See if we have all the data we need
        required_fields = ['terms_of_use', 'time_adj', 'carbs_being_eaten', 'carb_ratio_' + self.mealtime_prefix()]
        reply_dict = self.required_fields_process(required_fields)
        if reply_dict is not None:
            return reply_dict

        # 5. Give result
        correction = self.calc_insulin_for_carb_consumption()
        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.event().session().save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.event().session())

    def calc_insulin_for_carb_consumption(self):
        carbs_being_eaten = self.event().get_value_in_session(['carbs_being_eaten'])
        carb_ratio = self.event().get_value_in_session(['carb_ratio_' + self.mealtime_prefix()])
        correction = int(round(float(carbs_being_eaten) / float(carb_ratio), 0))
        self.event().set_value_in_session("mealtime", self.mealtime_prefix())
        self.event().set_value_in_session("carb_ratio", carb_ratio)
        self.event().set_value_in_session("correction", correction)
        return correction

    def bg_correction_with_carbs(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))
        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state(method_name):
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        carbs_being_eaten = self.event().value_for_slot_name('carbs_being_eaten')
        if carbs_being_eaten is not None:
            self.event().set_value_in_session('carbs_being_eaten', carbs_being_eaten)

        current_bg_level = self.event().value_for_slot_name('current_bg_level')
        if current_bg_level is not None:
            self.event().set_value_in_session('current_bg_level', current_bg_level)

        required_fields = ['terms_of_use', 'time_adj', 'carbs_being_eaten', 'current_bg_level',
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
        self.event().set_value_in_session("correction", correction)

        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.event().session().save()
        reply_intent_dict = intent_dict['conditions'][dose_no_dose]
        return Reply.build(reply_intent_dict, self.event().session())

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
        logger.debug("session={}".format(self.event().get_session_attributes()))
        logger.debug("request={}".format(self.event().request()))

        intent_dict = self.get_intent_details(method_name)

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != method_name:
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        requested_value = self.event().value_for_slot_name('agree')

        # 3. See if we have all the data we need
        # 4. Request data if needed
        if requested_value is None:
            reply_intent_dict = intent_dict['conditions']['listen']
            return Reply.build(reply_intent_dict, self.event().session())

        if requested_value == "agree":
            logger.debug('AGREED to AGREEMENT')
            date_str = datetime.date.today().strftime("%B %d, %Y")
            self.event().set_value_in_session('terms_of_use', date_str)
            self.event().session().save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        elif requested_value == "disagree":
            reply_intent_dict = intent_dict['conditions']['disagree']
        else:
            # We got a value in the slot but it is neither agree or disagree
            reply_intent_dict = intent_dict['conditions']['retry']

        return Reply.build(reply_intent_dict, self.event().session())

    def set_current_time(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.{}'.format(method_name))

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != method_name:
            return self.handle_session_end_confused()

        requested_value = self.event().value_for_slot_name('time')
        time_am_pm = self.event().value_for_slot_name('ampm')
        time_adj = TimeOfDay.time_adj(requested_value, time_am_pm)

        logger.debug(" time={} time_am_pm={} adj={}".format(requested_value, time_am_pm, time_adj))
        if time_adj is not None:
            self.event().set_value_in_session('time_adj', str(time_adj))
            self.event().session().save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        else:
            intent_dict = self.get_intent_details(method_name)
            return Reply.build(intent_dict['conditions']['retry'], self.event().session())

    def welcome_request(self, method_name=None):
        """ If we wanted to initialize the session to have some attributes we could
        add those here

        Args:
            method_name:
        """
        return self.handle_default_intent(method_name)

    def reset_stored_values(self, method_name=None):
        self.event().session().reset_stored_values()
        return self.handle_default_intent(method_name)

    def handle_session_end_request(self, method_name=None):
        return self.handle_default_intent(method_name)

    def handle_session_end_confused(self, method_name=None):
        logger.debug('**************** entering DiabetesDialog.handle_session_end_confused')
        logger.debug("session={}".format(self.event().get_session_attributes()))
        logger.debug("request={}".format(self.event().request()))
        # can we re_prompt?
        retry_attempted = self.event().get_value_in_session(["retry_attempted"])
        if retry_attempted is None:
            requested_value = self.event().get_value_in_session(['requested_value'])
            if requested_value:
                re_prompt = self.get_re_prompt_for_data(requested_value)
                if re_prompt:
                    prompt = Prompt.ssml(re_prompt)
                    reprompt = Prompt.ssml("Sorry I did not hear that. {}".format(re_prompt))
                    card = Card.simple("Redirect", re_prompt)
                    set_should_end_session = False
                    response = Response.constr(prompt, reprompt, card, set_should_end_session)
                    self.event().set_value_in_session("retry_attempted", True)
                    reply = Reply.constr(response, self.event().session())
                    return reply.json()

        # we are done
        established_dialog = self.peek_established_dialog()
        # print("established_dialog {}".format(established_dialog))
        text = 'no intent set'
        if established_dialog:
            text = established_dialog.replace("_", " ")
        self.event().set_value_in_session('confused', text)
        return self.handle_default_intent(method_name)

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

    def map_requested_value(self, from_initial_utterance):
        requested_name = self.event().get_value_in_session(['requested_value'])
        requested_value = self.event().value_for_slot_name('requested_value')
        if requested_value is not None:
            if requested_name is not None:
                self.event().set_value_in_session(requested_name, requested_value)
            else:
                self.event().set_value_in_session(from_initial_utterance, requested_value)

    def required_fields_process(self, required_fields):
        reply_dict = None
        for key in required_fields:
            value = self.event().get_value_in_session([key])
            logger.debug("      key   {}".format(key))
            logger.debug("      value {}".format(value))

            # 4. Request data if needed
            if value is None:
                logger.debug("      none condition key={}".format(key))
                expected_intent = self.get_expected_intent_for_data(key)
                self.push_established_dialog(expected_intent)
                self.event().set_value_in_session('requested_value', key)
                speech_output = self.get_prompt_for_data(key)
                prompt = Prompt.ssml(speech_output)
                reprompt = Prompt.ssml("Sorry I did not hear that. {}".format(speech_output))
                response = Response.constr(prompt, reprompt, card=None, should_end_session=False)
                reply = Reply.constr(response, self.event().get_session_attributes())
                reply_dict = reply.json()

        return reply_dict

    def day_night_prefix(self):
        time_adj = self.event().get_value_in_session(['time_adj'])
        prefix = 'night'
        if TimeOfDay.day_night(time_adj) == TimeOfDay.Daytime:
            prefix = 'day'
        return prefix

    def mealtime_prefix(self):
        time_adj = self.event().get_value_in_session(['time_adj'])
        if TimeOfDay.meal_time(time_adj) == TimeOfDay.Breakfast:
            prefix = 'breakfast'
        elif TimeOfDay.meal_time(time_adj) == TimeOfDay.Lunch:
            prefix = 'lunch'
        else:
            prefix = 'dinner'
        return prefix

    def execute_method(self, method_name):
        method = getattr(self, method_name)
        return method(method_name)
