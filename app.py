from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from StockPortfolio import StockPortfolio
import os
from typing import Optional
from admin import StockTransactionManager
from datetime import datetime,timezone

class StockPortfolioAPI:
    def __init__(self) -> None:
        """
        Initialize the StockPortfolioAPI instance.

        Args:
            file_path (str): The path to the file containing stock portfolio data.
        """
        self.portfolio: StockPortfolio = None
        
        self.admindb=StockTransactionManager()
        self.app: Flask = Flask(__name__)
        self.app.secret_key = "secret_key"  # Required for session management
        self.api_key: str = "joel09-02-2024Adh"  # Hardcoded API key
        self.df = None
        self.setup_routes()  # Initialize all routes

    def setup_routes(self) -> None:
        """
        Set up the routes for the Flask app.
        """
        @self.app.route("/")
        def index() -> str:
            """
            Render the home page.

            Returns:
                str: HTML content for the home page.
            """     
            
            if "user" in session:
                if "password" not in session:
                    session.pop('user',None)
                    return render_template("index.html")
                login=self.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    session.pop('user',None)
                    return render_template("index.html")
                if self.df is None:
                    self.df=self.admindb.transactions_to_dataframe()
                if self.portfolio is None or self.portfolio.user!=session["user"]:
                    self.portfolio = StockPortfolio(user=session["user"],dataframe=self.df) 
                           
            return render_template("index.html")

        @self.app.route("/stockDisplay")
        def stock_display() -> str:
            """
            Render the stock display page.

            Returns:
                str: HTML content for the stock display page.
            """
            if "user" in session:
                if "password" not in session:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                login=self.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                if self.df is None:
                    self.df=self.admindb.transactions_to_dataframe()
                if self.portfolio is None or self.portfolio.user!=session["user"]:
                    self.portfolio = StockPortfolio(user=session["user"],dataframe=self.df) 
            else:
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
                    
                    self.df=self.admindb.transactions_to_dataframe()
                    
                    session["user"] = username
                    session["password"] = password
                    
                    self.portfolio = StockPortfolio(user=username,dataframe=self.df) 
                    
                    return redirect(url_for("stock_display"))
                else:
                    session.pop("user", None)
                    self.admindb.logout()
                    flash("Invalid username or password")
                    login_failed = True  # Set flag to indicate failure
                    return redirect(url_for("login", login_failed=True))

            return render_template("login.html", login_failed=login_failed)
        
        @self.app.route("/signup", methods=["GET", "POST"])
        def signup():
            """
            Render the signup page and handle account creation.
            """
            if request.method == "POST":
                # Get form data
                username = request.form.get("username").strip()
                email = request.form.get("email").strip()
                password = request.form.get("password")
                confirm_password = request.form.get("confirm_password")

                # Validate input
                if not username or not email or not password or not confirm_password:
                    flash("All fields are required.", "error")
                    return render_template("signup.html")

                if password != confirm_password:
                    flash("Passwords do not match.", "error")
                    return render_template("signup.html")

                # Interact with StockTransactionManager to create an account
                try:
                    success = self.admindb.create_account(username=username, password=password, email=email)
                    if success:
                        flash("Account created successfully! Please log in.", "success")
                        return redirect(url_for("login"))
                    else:
                        flash("Username already exists. Please try a different username.", "error")
                except Exception as e:
                    flash(f"An error occurred: {str(e)}", "error")

            # Render the signup page for GET requests or failed POST submissions
            return render_template("signup.html")
        
        @self.app.route("/transaction", methods=["GET", "POST"])
        def transaction_form():
            """
            Handle displaying and submitting the stock transaction form.

            Returns:
                str: Rendered HTML page for GET requests, or redirects after POST.
            """
            if "user" in session:
                if "password" not in session:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                login=self.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
                if self.df is None:
                    self.df=self.admindb.transactions_to_dataframe()
                if self.portfolio is None or self.portfolio.user!=session["user"]:
                    self.portfolio = StockPortfolio(user=session["user"],dataframe=self.df) 
            else:
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

        @self.app.route("/api/transactionLogs", methods=["GET"])
        def get_transaction_logs() -> tuple:
            """
            Get the list of transactions by the user.

            Returns:
                tuple: JSON response with transaction logs or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            transactions = self.admindb.list_transactions()
            if transactions is not None:
                return jsonify(transactions.to_dict(orient="records"))
            return jsonify({"error": "No transaction data available"}), 404
        
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

        @self.app.route("/api/held_stocks", methods=["GET"])
        def get_held_stocks() -> tuple:
            """
            Get the list of held stocks in the portfolio.

            Returns:
                tuple: JSON response with held stocks data or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
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
            sold_stocks = self.portfolio.getSoldStocksData()
            if sold_stocks is not None:
                return jsonify(sold_stocks.to_dict(orient="records"))
            return jsonify({"error": "No sold stocks data available"}), 404
        
        @self.app.route("/api/unrealisedprofit", methods=["GET"])
        def get_unrealisedprofit() -> tuple:
            """
            Get the unrealized profit from the portfolio.

            Returns:
                tuple: JSON response with the unrealized profit or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            unrealized_profit = self.portfolio.getUnrealisedProfit()
            return jsonify({"unrealized_profit": unrealized_profit})
        
        @self.app.route("/api/onedreturns", methods=["GET"])
        def get_oneday_returns() -> tuple:
            """
            Get the one day returns from the portfolio.

            Returns:
                tuple: JSON response with the one day returns or error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403
            one_day_returns = self.portfolio.getOneDayReturns()
            return jsonify({"todays_returns": one_day_returns})
        
        @self.app.route("/api/submit_transactions", methods=["POST"])
        def submit_transactions():
            """
            Endpoint to handle submitted transaction data.
            """
            if not api.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403

            # Get JSON data from the POST request
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "Invalid data"}), 400

            try:
                
                def formatter(data):
                    converted_data = []
                    for entry in data:
                        # Convert date string to DatetimeWithNanoseconds format
                        date_object = datetime.strptime(entry['Date'], '%d-%m-%Y').replace(tzinfo=timezone.utc)
                        converted_entry = {
                            'Sl_No': entry['Sl.No.'],  # Rename to camelCase
                            'Date': date_object,  # Convert to datetime object
                            'Share': entry['Share'],
                            'Symbol': entry['Symbol'],
                            'Transaction': entry['Transaction'].lower(),  # Convert to lowercase
                            'Count': entry['Count'],
                            'Price': float(entry['Price']),  # Ensure float type for price
                            'Total_Amount': float(entry['Total Amount'])  # Rename to camelCase
                        }
                        converted_data.append(converted_entry)
                    return converted_data
                
                update= self.admindb.replace_transaction_history(formatter(data))
                
                if update:
                    self.df = self.admindb.transactions_to_dataframe()
                    self.portfolio = StockPortfolio(user=session["user"],dataframe=self.df) 
                    return jsonify({"message": "Transactions updated successfully"}), 200
                else:
                    return jsonify({"error": "Failed to update transactions"}), 500
            except Exception as e:
                
                return jsonify({"error": f"An error occurred: {str(e)}"}), 500


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
    api = StockPortfolioAPI()
    port: int = int(os.environ.get("PORT", 8000))
    api.run(debug=True, host="0.0.0.0", port=port)

# Expose the Flask app instance for Waitress
api = StockPortfolioAPI()
app = api.app