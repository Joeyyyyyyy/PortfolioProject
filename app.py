from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash, g
from StockPortfolio import StockPortfolio,MarketStatus
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
        self.app: Flask = Flask(__name__)
        self.app.secret_key = "secret_key"  # Required for session management
        self.api_key: str = "joel09-02-2024Adh"  # Hardcoded API key
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
            if "password" not in session:
                session.pop('user',None)
                           
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
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
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
                
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=username,password=password)

                if login == True:  
                    print(username+" has logged in.")
                    g.df=g.admindb.transactions_to_dataframe()
                    
                    session["user"] = username
                    session["password"] = password
                    
                    g.portfolio = StockPortfolio(user=username,dataframe=g.df) 
                    
                    return redirect(url_for("stock_display"))
                else:
                    session.pop("user", None)
                    g.admindb.logout()
                    flash("Invalid username or password")
                    login_failed = True  
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
                    g.admindb=StockTransactionManager()
                    success = g.admindb.create_account(username=username, password=password, email=email)
                    if success:
                        flash("Account created successfully! Please log in.", "success")
                        return redirect(url_for("login"))
                    else:
                        flash("Username already exists. Please try a different username.", "error")
                except Exception as e:
                    flash(f"An error occurred: {str(e)}", "error")

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
                g.admindb=StockTransactionManager()
                login=g.admindb.login(username=session["user"],password=session["password"])
                if login == False:
                    flash("Please log in to access this page.")
                    session.pop("user",None)
                    return redirect(url_for("login"))
            else:
                return redirect(url_for("login"))

            if request.method == "POST":
                pass
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
            g.admindb=StockTransactionManager()
            g.admindb.login(username=session["user"],password=session["password"])
            transactions = g.admindb.list_transactions()
            if transactions is not None:
                return jsonify(transactions.to_dict(orient="records"))
            return jsonify({"error": "No transaction data available"}), 404
        
        @self.app.route("/api/market_status",methods=["GET"])
        def get_market_status() -> tuple:
            """
            Returns the market status
            
            Returns:
                bool: True if market is open and False if market is closed.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}),403
            g.status=MarketStatus()
            g.marketopen=g.status.is_market_open()
            return jsonify({"market_status":g.marketopen})
        
        @self.app.route("/api/portfolio_data", methods=["GET"])
        def get_portfolio_data() -> tuple:
            """
            Get all portfolio data in a single response.

            Returns:
                tuple: JSON response with all portfolio data or an error message.
            """
            if not self.is_authorized(request):
                return jsonify({"error": "Unauthorized"}), 403

            try:
                # Initialize and prepare portfolio
                g.admindb = StockTransactionManager()
                g.admindb.login(username=session["user"], password=session["password"])
                g.df = g.admindb.transactions_to_dataframe()
                g.portfolio = StockPortfolio(user=session["user"], dataframe=g.df)
                g.portfolio.run()

                # Collect all data
                portfolio_data = {
                    "realized_profit": g.portfolio.getRealisedProfit(),
                    "unrealized_profit": g.portfolio.getUnrealisedProfit(),
                    "todays_returns": g.portfolio.getOneDayReturns(),
                    "held_stocks": g.portfolio.getHeldStocks().to_dict(orient="records") if g.portfolio.getHeldStocks() is not None else [],
                    "sold_stocks": g.portfolio.getSoldStocksData().to_dict(orient="records") if g.portfolio.getSoldStocksData() is not None else []
                }

                return jsonify(portfolio_data)

            except Exception as e:
                # Handle errors gracefully
                return jsonify({"error": str(e)}), 500
        
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
                g.admindb=StockTransactionManager()
                g.admindb.login(username=session["user"],password=session["password"])
                update= g.admindb.replace_transaction_history(formatter(data))
                
                if update:
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