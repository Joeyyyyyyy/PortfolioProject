from flask import Flask, jsonify, request, render_template
from StockPortfolio import StockPortfolio
import os

class StockPortfolioAPI:
    def __init__(self, file_path="TransactionDeets.xlsx"):
        self.app = Flask(__name__)
        self.portfolio = StockPortfolio(file_path=file_path)
        self.portfolio.run()  # Pre-calculate values for fast access
        self.setup_routes()   # Initialize all routes

    def setup_routes(self):
        @self.app.route("/")
        def home():
            return render_template("index.html")

        @self.app.route("/stockDisplay")
        def stock_display():
            return render_template("stockDisplay.html")
        
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route("/api/held_stocks", methods=["GET"])
        def get_held_stocks():
            self.portfolio.run()
            held_stocks = self.portfolio.getHeldStocks()
            if held_stocks is not None:
                return jsonify(held_stocks.to_dict(orient="records"))
            return jsonify({"error": "No held stocks data available"}), 404

        @self.app.route("/api/sold_stocks", methods=["GET"])
        def get_sold_stocks():
            self.portfolio.run()
            sold_stocks = self.portfolio.getSoldStocksData()
            if sold_stocks is not None:
                return jsonify(sold_stocks.to_dict(orient="records"))
            return jsonify({"error": "No sold stocks data available"}), 404

        @self.app.route("/api/profit", methods=["GET"])
        def get_profit():
            self.portfolio.run()
            realized_profit = self.portfolio.getRealisedProfit()
            return jsonify({"realized_profit": realized_profit})

    def run(self, debug=True, host="127.0.0.1", port=5000):
        self.app.run(debug=debug,host=host,port=port)


# To run the API
if __name__ == "__main__":
    api = StockPortfolioAPI()
    port = int(os.environ.get("PORT", 5000))
    api.run(debug=False,host="0.0.0.0", port=port)
