import schedule
from trading.calc_signal import trade_signal

def main():
    times = ["00:10", "15:10", "30:10", "45:10"]
    for t in times:
        schedule.every().hour.at(t).do(trade_signal)
    while True:
        schedule.run_pending()

if __name__ == "__main__":
    main()