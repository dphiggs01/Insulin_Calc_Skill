import logging
from pydblite.pydblite import Base

logger = logging.getLogger()


class ZipcodeDB(object):
    PYDBLITE_DB_FILE = './zipcode.db'

    def __init__(self,pydblite_db_file=None):
        if pydblite_db_file is None:
            pydblite_db_file = ZipcodeDB.PYDBLITE_DB_FILE
        try:
            self._db = Base(pydblite_db_file)
            self._db.open()
        except Exception:
            self._db = None

    def query_by_zip_code(self, zip_cd):
        logger.debug("**************** entering ZipcodeDB.query_zipcode_db_by_zip_code")
        record = {} # Empty dict if not found
        if self._db is not None:
            records = self._db(zip_cd=zip_cd)
            if len(records)==1:
                record = records[0]
        return record

    def get_timezone_for_zip_code(self, zip_code):
        logger.debug("**************** entering ZipcodeDB.get_timezone")

        ret_val = 'NoTZ/'+zip_code
        data = self.query_by_zip_code(zip_code)
        if data:
            # timezone is really just an offset
            timezone = data['data']['timezone']
            dst = data['data']['dst']
            tz_dic = {'-5+1':'US/Eastern', '-5+0':'US/East-Indiana', '-6+1':'US/Central', '-7+1':'US/Mountain',
                      '-7+0':'US/Arizona', '-8+1':'US/Pacific', '-9+1':'US/Alaska', '-10+0':'US/Hawaii',
                      '-10+1':'US/Aleutian'}
            key=timezone+'+'+dst
            if key in tz_dic:
                ret_val = tz_dic[key]

        return ret_val

