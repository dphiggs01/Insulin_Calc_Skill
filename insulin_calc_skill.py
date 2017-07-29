from ask_amy.state_mgr.stack_dialog_mgr import StackDialogManager
from ask_amy.state_mgr.stack_dialog_mgr import required_fields
from ask_amy.core.reply import Reply
import logging
from ask_amy.utilities.time_of_day import TimeOfDay
from ask_amy.utilities.account_link import AmazonProfile
from zip_code_db import ZipcodeDB

logger = logging.getLogger()


class InsulinCalcSkill(StackDialogManager):
    def new_session_started(self):
        logger.debug("**************** entering DiabetesDialog.new_session_started")

        if not self.session.attribute_exists('time_zone'):
            if self.session.access_token is not None:
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

    @required_fields(['time_adj'], user_managed=True)
    def blood_glucose_correction(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        time_adj = self.session.attributes['time_adj']
        day_night = TimeOfDay.day_night(time_adj)
        self.session.attributes['day_night'] = day_night
        required = ['time_adj', 'current_bg_level', 'target_bg_level_' + day_night, 'correction_factor_' + day_night]
        return self.process_request(required, self.calc_blood_glucose_correction)

    def calc_blood_glucose_correction(self, called_from_wrapper=None):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, 'calc_blood_glucose_correction'))
        suffix = self.session.attributes['day_night']
        current_bg_level = self.request.attributes['current_bg_level']
        target_bg_level = self.request.attributes['target_bg_level_' + suffix]
        correction_factor = self.request.attributes['correction_factor_' + suffix]

        # Move fields_to_persist to the session scope for db persistence
        self.session.attributes['target_bg_level_' + suffix] = target_bg_level
        self.session.attributes['correction_factor_' + suffix] = correction_factor

        correction = int(round((float(current_bg_level) - float(target_bg_level)) / float(correction_factor), 0))
        time_adj = self.session.attributes['time_adj']
        self.request.attributes['current_time'] = TimeOfDay.current_time(time_adj)
        self.request.attributes['target_bg_level'] = target_bg_level
        self.request.attributes['correction_factor'] = correction_factor
        self.request.attributes['correction'] = correction
        return correction

    @required_fields(['time_adj'], user_managed=True)
    def insulin_for_carb_consumption(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        time_adj = self.session.attributes['time_adj']
        mealtime = TimeOfDay.meal_time(time_adj)
        self.session.attributes['mealtime'] = mealtime
        required = ['time_adj', 'carbs_being_eaten', 'carb_ratio_' + mealtime]
        return self.process_request(required, self.calc_insulin_for_carb_consumption)

    def calc_insulin_for_carb_consumption(self, called_from_wrapper=None):
        suffix = self.session.attributes['mealtime']
        amt_of_carbs = self.request.attributes['carbs_being_eaten']
        carb_ratio = self.request.attributes['carb_ratio_' + suffix]

        # Move fields_to_persist to the session scope for db persistence
        self.session.attributes['carb_ratio_' + suffix] = carb_ratio
        correction = int(round(float(amt_of_carbs) / float(carb_ratio), 0))
        self.request.attributes['carb_ratio'] = carb_ratio
        self.request.attributes['correction'] = correction
        return correction

    @required_fields(['time_adj'], user_managed=True)
    def bg_correction_with_carbs(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        time_adj = self.session.attributes['time_adj']
        mealtime = TimeOfDay.meal_time(time_adj)
        day_night = TimeOfDay.day_night(time_adj)
        self.session.attributes['mealtime'] = mealtime
        self.session.attributes['day_night'] = day_night

        required = ['time_adj', 'current_bg_level', 'carbs_being_eaten', 'target_bg_level_' + day_night,
                    'correction_factor_' + day_night, 'carb_ratio_'+mealtime]
        return self.process_request(required, self.calc_bg_correction_with_carbs)

    def calc_bg_correction_with_carbs(self, called_from_wrapper=None):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        bg_correction = self.calc_blood_glucose_correction()
        carb_correction = self.calc_insulin_for_carb_consumption()
        correction = carb_correction
        if bg_correction > 0:
            correction += bg_correction
        self.session.attributes['correction'] = correction
        return correction

    def set_current_time(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        # is this a good state?
        established_dialog = self.peek_established_dialog()
        state_good = True
        if established_dialog is None:
            state_good = False
        else:
            if established_dialog['intent_name'] != self.intent_name:
                state_good = False

        if state_good:
            self.slot_data_to_intent_attributes()

            time_adj = None
            if 'time' in established_dialog and 'ampm' in established_dialog:
                time_hour_min = established_dialog['time']
                time_am_pm = established_dialog['ampm']
                time_adj = TimeOfDay.time_adj(time_hour_min, time_am_pm)

            if time_adj is not None:
                self.pop_established_dialog()
                self.session.attributes['time_adj'] = str(time_adj)
                self.session.save()
                established_dialog = self.peek_established_dialog()
                logger.debug("**************** established_dialog {}".format(established_dialog))
                self._intent_name = established_dialog['intent_name']
                return self.execute_method(self._intent_name)
            else:
                reply_dialog = self.reply_dialog[self.intent_name]
                return Reply.build(reply_dialog['conditions']['retry'], self.event)
        else:
            return self.handle_session_end_confused()

    def help_intent(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        self.reset_established_dialog()
        return self.handle_default_intent()

    def account_link_intent(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        return self.handle_default_intent()

    def reset_stored_values(self):
        logger.debug("**************** entering {}.{}".format(self.__class__.__name__, self.intent_name))
        self.session.reset_stored_values()
        return self.handle_default_intent()

    #  Helper function to process calculations and required fields
    def process_request(self, required, function):
        required_fields_fun = required_fields(required)
        #  call @required_fields decorator directly so we can add tne suffix to the correction_factor_
        wrapper_fun = required_fields_fun(function)
        response = wrapper_fun(self)
        if isinstance(response, dict):
            return response
        else:
            dose_no_dose = 'dose'
            if response <= 0:
                dose_no_dose = 'no_dose'

            self.session.save()
            reply_dialog = self.reply_dialog[self.intent_name]
            return Reply.build(reply_dialog['conditions'][dose_no_dose], self.event)
