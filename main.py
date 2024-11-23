from trading.calc_signal import trade_signal
from data.stream_data import stream_data
import schedule

def main():
    stream_data()

    times = ["00:10", "15:10", "30:10", "45:10"]
    for t in times:
        schedule.every().hour.at(t).do(trade_signal)
    while True:
        schedule.run_pending()

if __name__ == "__main__":
    main()