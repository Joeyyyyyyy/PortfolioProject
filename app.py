from flask import Flask, jsonify, request, render_template
from StockPortfolio import StockPortfolio

app = Flask(__name__)

portfolio = StockPortfolio(file_path="TransactionDeets.xlsx")
portfolio.run()  # Pre-calculate values for fast access

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/held_stocks", methods=["GET"])
def get_held_stocks():
    held_stocks = portfolio.getHeldStocks()
    if held_stocks is not None:
        return jsonify(held_stocks.to_dict(orient="records"))
    return jsonify({"error": "No held stocks data available"}), 404

@app.route("/api/profit", methods=["GET"])
def get_profit():
    realized_profit = portfolio.getRealisedProfit()
    return jsonify({"realized_profit": realized_profit})

if __name__ == "__main__":
    app.run(debug=True)