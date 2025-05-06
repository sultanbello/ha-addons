from inspect import getframeinfo, stack
from datetime import datetime
import os
import sys

print('Loading Logger')

class Logger:
    def __init__(self, parent):
        self.log_level  = parent.log_level
        self.parent     = parent

    def log_message(self, msg='', type = 'Info'):
        msg     = str(msg)
        type    = str(type).lower()

        if(
            self.log_level == 'debug' and not self.parent.debug or
            self.log_level != 'info' and type == 'info' or
            self.log_level == 'warning' and type == 'info' or
            self.log_level == 'error' and type != 'error'
        ):
            return

        try:
            date        = datetime.strftime(datetime.now(), '%d-%m-%Y %H:%M')
            caller      = getframeinfo(stack()[1][0])
            location    = f'{os.path.basename(caller.filename)}:{caller.lineno} -'.ljust(25)

            if msg == '':
                log_msg = "\n\n"
            else:
                log_msg     = f'{date} - {location}' + type.ljust(7) + ' - ' + msg

            warning     = '\033[93m'
            error       = '\033[91m'
            endc        = '\033[0m'

            if type == 'error':
                print(f"{error}{log_msg}{endc}")
            elif type == 'warning':
                print(f"{warning}{log_msg}{endc}")
            else:
                print(log_msg)

            f   = open('/share/birthdays_debug.log', "a", encoding="utf-8")
            f.write(log_msg + "\n")
            f.close()
                
        except Exception as e:
            print(f"Logger.py - Error - {str(e)} on line {sys.exc_info()[-1].tb_lineno}") 