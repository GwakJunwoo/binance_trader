from .cli import main
if __name__ == "__main__":
    main(["backtest", "--symbol", "BTCUSDT", "--interval", "1m", "--data", "data/BTCUSDT_1m.csv"])
