from misc.load_data import job
import schedule
import time

times = [":00", ":15", ":30", ":45"]
for t in times:
    schedule.every().hour.at(t).do(lambda: job('15m'))

schedule.every().hour.at(":00").do(lambda: job('1h'))

while True:
    time.sleep(5)
    schedule.run_pending()