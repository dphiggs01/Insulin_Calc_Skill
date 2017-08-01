from ask_amy.utilities.slot_validator import Slot_Validator
import logging
from datetime import datetime

logger = logging.getLogger()

VALID = 0  # Passed validation
MSG_01_TEXT = 1  # Failed Validation
MSG_02_TEXT = 2  # Failed Validation
MSG_03_TEXT = 3  # Failed Validation
MSG_04_TEXT = 4  # Failed Validation


class ValidRangeBG(Slot_Validator):

    def is_valid_value(self, value):
        logger.debug("**************** entering ValidRageBG.is_valid_value")

        if isinstance(value, str):
            try:
                value = int(value)
                if value == 0:
                    status_code = MSG_02_TEXT
                elif value >= 1000:
                    status_code = MSG_01_TEXT
                else:
                    status_code = VALID
            except ValueError:
                logger.debug("Failed to convert to number {}".format(value))
                status_code = MSG_03_TEXT

        return status_code


class ValidRangeBGTarget(Slot_Validator):

    def is_valid_value(self, value):
        logger.debug("**************** entering ValidRangeBGTarget.is_valid_value")
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            try:
                value = int(value)
                if 50 <= value <= 250:
                    status_code = VALID

            except ValueError:
                logger.debug("Failed to convert to number {}".format(value))
                status_code = MSG_03_TEXT

        return status_code

class ValidRangeBGFactor(Slot_Validator):

    def is_valid_value(self, value):
        logger.debug("**************** entering ValidRangeBGFactor.is_valid_value")
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            try:
                value = int(value)
                if 15 <= value <= 90:
                    status_code = VALID

            except ValueError:
                logger.debug("Failed to convert to number {}".format(value))
                status_code = MSG_03_TEXT

        return status_code

class ValidRangeBGRatio(Slot_Validator):

    def is_valid_value(self, value):
        logger.debug("**************** entering ValidRangeBGRatio.is_valid_value")
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            try:
                value = int(value)
                if 5 <= value <= 25:
                    status_code = VALID

            except ValueError:
                logger.debug("Failed to convert to number {}".format(value))
                status_code = MSG_03_TEXT

        return status_code

class ValidRangeCalories(Slot_Validator):

    def is_valid_value(self, value):
        logger.debug("**************** entering ValidRangeCalories.is_valid_value")
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            try:
                value = int(value)
                if 1 < value <= 3000:
                    status_code = VALID

            except ValueError:
                logger.debug("Failed to convert to number {}".format(value))
                status_code = MSG_03_TEXT

        return status_code



