from datetime import datetime

if __name__ != "__main__":
    print("run_schedule cannot be imported!")
    exit()

day = datetime.now().weekday()

if day == 1:  # Monday
    print("Weekly reward distribution!")

    import handle_distribution

    handle_distribution.start()
elif day == 7:  # Sunday
    print("Reminding lumenauts to set their account!")

    import handle_acc_missing_warning

    handle_acc_missing_warning.start()
else:
    print("Nothing to do today!")
