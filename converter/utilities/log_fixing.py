import sys
import os
import logging
import inspect
import datetime

sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')

log_path = paths.LOG_PATH
if not os.path.exists(log_path):
    os.makedirs(log_path)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H:%M:%S")
logging_path = os.path.join(log_path, "automation_{}.txt".format(timestamp))
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def test_log_function():
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Test function running -> {}'.format(function_name))
    logging.info('Doing something')
