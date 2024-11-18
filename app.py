from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from StockPortfolio import StockPortfolio
import os
from typing import Optional
from admin import StockTransactionManager

class StockPortfolioAPI:
    def __init__(self, file_path: str = None) -> None:
        """
        Initialize the StockPortfolioAPI instance.

        Args:
            file_path (str): The path to the file containing stock portfolio data.
        """
        self.portfolio: StockPortfolio = None
        self.file_path=file_path
        
        self.admindb=StockTransactionManager()
        self.app: Flask = Flask(__name__)
        self.app.secret_key = "secret_key"  # Required for session management
        self.api_key: str = "joel09-02-2024Adh"  # Hardcoded API key
        self.setup_routes()  # Initialize all routes

    def setup_routes(self) -> None:
        """
        Set up the routes for the Flask app.
        """
        @self.app.route("/")
        def home() -> str:
            """
            Render the home page.

            Returns:
                str: HTML content for the home page.
            """
            return render_template("index.html")
        
        @self.app.route("/")
        def index() -> str:
            """
            Render the home page.

            Returns:
                str: HTML content for the home page.
            """
            return render_template("index.html")

        @self.app.route("/stockDisplay")
        def stock_display() -> str:
            """
            Render the stock display page.

            Returns:
                str: HTML content for the stock display page.
            """
            if "user" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login"))
            return render_template("stockDisplay.html")

        @self.app.route("/login", methods=["GET", "POST"])
        def login() -> str:
            """
            Handle login form submission and render login page.
            """
            login_failed = request.args.get("login_failed", default=False, type=lambda v: v.lower() == "true")  # Initialize the flag
            
            if request.method == "POST":
                username = request.form.get("username").strip()
                password = request.form.get("password")
                
                login=self.admindb.login(username=username,password=password)

                # Authentication logic (Replace with real authentication)
                if login == True:  # Example credentials
                    
                    df=self.admindb.transactions_to_dataframe()
                    
                    session["user"] = username
                    
                    self.portfolio = StockPortfolio(dataframe=df)
                    if(self.file_path!=None):
                        self.portfolio.run()  # Pre-calculate values for fast access
                    
                    return redirect(url_for("stock_display"))
                else:
                    session.pop("user", None)
                    flash("Invalid username or password")
                    login_failed = True  # Set flag to indicate failure
                    return redirect(url_for("login", login_failed=True))

            return render_template("login.html", login_failed=login_failed)
        
        @self.app.route("/transaction", methods=["GET", "POST"])
        def transaction_form():
            """
            Handle displaying and submitting the stock transaction form.

            Returns:
                str: Rendered HTML page for GET requests, or redirects after POST.
            """
            if "user" not in session:
                flash("Please log in to access this page.")
                return redirect(url_for("login"))

            if request.method == "POST":
                pass
                #Enter POST LOGIC
            # For GET requests, render the transaction form
            return render_template("transaction.html")

        @self.app.route("/logout")
        def logout() -> str:
            """
            Clear the session and log the user out.
            """
            session.pop("user", None)
            flash("You have been logged out.")
            return redirect(url_for("home"))

        @self.app.route("/api/held_stocks", methods=["GET"])
        def get_held_stocks() -> tuple:
            """
            Get the list of held stocks in the portfolio.

            Returns:
                tuple: JSON response with held stocks data or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            self.portfolio.run()
            held_stocks = self.portfolio.getHeldStocks()
            if held_stocks is not None:
                return jsonify(held_stocks.to_dict(orient="records"))
            return jsonify({"error": "No held stocks data available"}), 404

        @self.app.route("/api/sold_stocks", methods=["GET"])
        def get_sold_stocks() -> tuple:
            """
            Get the list of sold stocks in the portfolio.

            Returns:
                tuple: JSON response with sold stocks data or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            self.portfolio.run()
            sold_stocks = self.portfolio.getSoldStocksData()
            if sold_stocks is not None:
                return jsonify(sold_stocks.to_dict(orient="records"))
            return jsonify({"error": "No sold stocks data available"}), 404

        @self.app.route("/api/profit", methods=["GET"])
        def get_profit() -> tuple:
            """
            Get the realized profit from the portfolio.

            Returns:
                tuple: JSON response with the realized profit or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            self.portfolio.run()
            realized_profit = self.portfolio.getRealisedProfit()
            return jsonify({"realized_profit": realized_profit})

    def is_authorized(self, request) -> bool:
        """
        Check if the request contains the correct API key.

        Args:
            request : The Flask request object.

        Returns:
            bool: True if authorized, False otherwise.
        """
        api_key: Optional[str] = request.headers.get("x-api-key")
        return api_key == self.api_key

    def run(self, debug: bool = True, host: str = "127.0.0.1", port: int = 5000) -> None:
        """
        Run the Flask app.

        Args:
            debug (bool): Whether to run the app in debug mode.
            host (str): The hostname to listen on.
            port (int): The port of the web server.
        """
        self.app.run(debug=debug, host=host, port=port)


# To run the API
if __name__ == "__main__":
    api = StockPortfolioAPI(file_path="TransactionDeets.xlsx")
    port: int = int(os.environ.get("PORT", 8000))
    api.run(debug=True, host="0.0.0.0", port=port)
