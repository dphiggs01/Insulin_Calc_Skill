import logging
import datetime
from ask_amy.state_mgr.stack_dialog_mgr import StackDialogManager
from ask_amy.core.reply import Reply
from ask_amy.utilities.time_of_day import TimeOfDay
from ask_amy.utilities.account_link import AmazonProfile
from zip_code_db import ZipcodeDB

logger = logging.getLogger()


class DiabetesDialog(StackDialogManager):
    def new_session_started(self):
        logger.debug("**************** entering DiabetesDialog.new_session_started")

        if not self.session.attribute_exists('time_adj'):
            # If we do not have a time adj offset see if we can derive one from timezone
            if not self.session.attribute_exists('time_zone') and self.session.access_token is not None:
                # If we do not have a timezone see if we have access to the amazon profile to get one
                amazon_profile = AmazonProfile(self.session.access_token)
                zip_code = amazon_profile.get_zip_code()
                zip_code_db = ZipcodeDB()
                timezone = zip_code_db.get_timezone_for_zip_code(zip_code)
                self.session.attributes['time_zone'] = timezone

            if self.session.attribute_exists('time_zone'):
                time_adj = TimeOfDay.time_adj_given_tz(self.session.attributes['time_zone'])
                if time_adj is not None:
                    self.session.attributes['time_adj'] = time_adj

    def launch_request(self):
        logger.debug("**************** entering DiabetesDialog.launch_request")
        self._intent_name = 'welcome_request'
        return self.handle_default_intent()

    def blood_glucose_correction(self):
        logger.debug('**************** entering DiabetesDialog.blood_glucose_correction')

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state():
            return self.handle_session_end_confused()

        # 2. See if we have any slots filled
        self.event.slot_data_to_session_attributes()

        # 3. See if we have all the data we need
        required_fields = ['time_adj', 'current_bg_level', 'target_bg_level_' + self.day_night_prefix(),
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
        reply_dialog = self.reply_dialog[self.intent_name]
        return Reply.build(reply_dialog['conditions'][dose_no_dose], self.session)

    def calc_blood_glucose_correction(self):
        current_bg_level = self.session.attributes['current_bg_level']
        target_bg_level = self.session.attributes['target_bg_level_' + self.day_night_prefix()]
        correction_factor = self.session.attributes['correction_factor_' + self.day_night_prefix()]
        correction = int(round((float(current_bg_level) - float(target_bg_level)) / float(correction_factor), 0))
        time_adj = self.session.attributes['time_adj']
        self.session.attributes['current_time'] = TimeOfDay.current_time(time_adj)
        self.session.attributes['day_night'] = self.day_night_prefix()
        self.session.attributes['target_bg_level'] = target_bg_level
        self.session.attributes['correction_factor'] = correction_factor
        self.session.attributes['correction'] = correction
        return correction

    def insulin_for_carb_consumption(self):
        logger.debug('**************** entering DiabetesDialog.insulin_for_carb_consumption')

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state():
            return self.handle_session_end_confused()

        # 2. See if we have any slots filled
        self.event.slot_data_to_session_attributes()

        # 3. See if we have all the data we need
        required_fields = ['time_adj', 'amt_of_carbs', 'carb_ratio_' + self.mealtime_prefix()]
        reply_dict = self.required_fields_process(required_fields)
        if reply_dict is not None:
            return reply_dict

        # 5. Give result
        correction = self.calc_insulin_for_carb_consumption()
        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.session.save()
        reply_dialog = self.reply_dialog[self.intent_name]
        return Reply.build(reply_dialog['conditions'][dose_no_dose], self.session)

    def calc_insulin_for_carb_consumption(self):
        amt_of_carbs = self.session.attributes['amt_of_carbs']
        carb_ratio = self.session.attributes['carb_ratio_' + self.mealtime_prefix()]
        correction = int(round(float(amt_of_carbs) / float(carb_ratio), 0))
        self.session.attributes['mealtime'] = self.mealtime_prefix()
        self.session.attributes['carb_ratio'] = carb_ratio
        self.session.attributes['correction'] = correction
        return correction

    def bg_correction_with_carbs(self):
        logger.debug('**************** entering DiabetesDialog.bg_correction_with_carbs')

        # 1. Check the state of the conversation and react if things smell funny
        if not self.is_good_state():
            return self.handle_session_end_confused()

        # 2. See if we have any slots filled
        self.event.slot_data_to_session_attributes()

        required_fields = ['time_adj', 'amt_of_carbs', 'current_bg_level',
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
        self.session.attributes['correction'] = correction

        dose_no_dose = 'dose'
        if correction <= 0:
            dose_no_dose = 'no_dose'

        self.session.save()
        reply_dialog = self.reply_dialog[self.intent_name]
        return Reply.build(reply_dialog['conditions'][dose_no_dose], self.session)

    def requested_value_intent(self):
        logger.debug('**************** entering DiabetesDialog.requested_value_intent')

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        logger.debug('**************** XXXXXXXX established_dialog={} intent_name={}'.format(established_dialog,
                                                                                             self.intent_name))
        if established_dialog != self.intent_name:
            return self.handle_session_end_confused()
        else:
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            self._intent_name = established_dialog
            return self.execute_method(established_dialog)

    def agree_to_terms(self):
        logger.debug('**************** entering DiabetesDialog.agree_to_terms')

        reply_dialog = self.reply_dialog[self.intent_name]

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != self.intent_name:
            return self.handle_session_end_confused()

        # 2. See if we got any slots filled
        requested_value = self.request.value_for_slot_name('terms_of_use')

        # 3. See if we have all the data we need
        # 4. Request data if needed
        if requested_value is None:
            return Reply.build(reply_dialog['conditions']['listen'], self.session)

        if requested_value == "agree":
            date_str = datetime.date.today().strftime("%B %d, %Y")
            self.session.attributes['terms_of_use'] = date_str
            self.session.save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        elif requested_value == "disagree":
            return Reply.build(reply_dialog['conditions']['disagree'], self.session)
        else:
            # We got a value in the slot but it is neither agree or disagree
            return Reply.build(reply_dialog['conditions']['retry'], self.session)

    def set_current_time(self):
        logger.debug('**************** entering DiabetesDialog.set_current_time')

        # 1. Check the state of the conversation and react if things smell funny
        established_dialog = self.peek_established_dialog()
        if established_dialog != self.intent_name:
            return self.handle_session_end_confused()

        requested_value = self.request.value_for_slot_name('time')
        time_am_pm = self.request.value_for_slot_name('ampm')
        time_adj = TimeOfDay.time_adj(requested_value, time_am_pm)

        if time_adj is not None:
            self.session.attributes['time_adj'] = str(time_adj)
            self.session.save()
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            return self.execute_method(established_dialog)
        else:
            reply_dialog = self.reply_dialog[self.intent_name]
            return Reply.build(reply_dialog['conditions']['retry'], self.session)

    def help_request(self):
        """ Reset any establish conversation and play help message
        """
        self.reset_established_dialog()
        return self.handle_default_intent()

    def reset_stored_values(self):
        self.session.reset_stored_values()
        return self.handle_default_intent()

    def handle_session_end_request(self):
        return self.handle_default_intent()

    def day_night_prefix(self):
        time_adj = self.session.attributes['time_adj']
        prefix = 'night'
        if TimeOfDay.day_night(time_adj) == TimeOfDay.Daytime:
            prefix = 'day'
        return prefix

    def mealtime_prefix(self):
        time_adj = self.session.attributes['time_adj']
        if TimeOfDay.meal_time(time_adj) == TimeOfDay.Breakfast:
            prefix = 'breakfast'
        elif TimeOfDay.meal_time(time_adj) == TimeOfDay.Lunch:
            prefix = 'lunch'
        else:
            prefix = 'dinner'
        return prefix

