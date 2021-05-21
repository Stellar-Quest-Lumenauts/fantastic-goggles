from datetime import datetime

from handlers import distribution
from handlers import account_missing_warning

if __name__ != "__main__":
    print("run_schedule cannot be imported!")
    exit()

day = datetime.now().weekday()

if day == 1:  # Monday
    print("Weekly reward distribution!")
    distribution.start()
elif day == 7:  # Sunday
    print("Reminding lumenauts to set their account!")
    account_missing_warning.start()
else:
    print("Nothing to do today!")
