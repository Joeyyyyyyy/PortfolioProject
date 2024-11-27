import uuid
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd
from typing import Optional, Dict

class StockTransactionManager:
    """A manager class for handling user accounts and stock transactions in Firebase Firestore."""

    def __init__(self) -> None:
        """
        Initialize StockTransactionManager with Firebase credentials.

        Args:
            service_account_path (Dict[str, str]): Firebase service account credentials as a dictionary.
        """
        
        load_dotenv()
        # Store all variables in a single dictionary
        service_account_path = {
            "type": os.getenv("TYPE"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": os.getenv("PRIVATE_KEY"),
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
        }

        app_name = f"app_{uuid.uuid4().hex}"  # Generate a unique name
        self.app=self._initialize_firebase(service_account_path, app_name=app_name)
        self.db = firestore.client(app=self.app)
        self.current_user = None

    def _initialize_firebase(self, service_account_path: Dict[str, str],app_name:str) -> None:
        """
        Initialize the Firebase app with the provided service account credentials.

        Args:
            service_account_path (Dict[str, str]): Firebase service account credentials as a dictionary.
        """
        cred = credentials.Certificate(service_account_path)
        app=firebase_admin.initialize_app(cred,name=app_name)
        return app

    def create_account(self, username: str, password: str, email: str = None, lastindex: int = 1) -> bool:
        """
        Create a new user account.

        Args:
            username (str): Username for the new account.
            password (str): Password for the new account.
            email (str): E-mail of the account user.
            lastindex (int): (Optional) Index of the first entry. Set to 1 by default.

        Returns:
            bool: True if the account was created successfully, False otherwise.
        """
        user_data = self._get_user_data(username)
        if user_data:
            print("Username already exists.")
            return False
        else:
            self._insert_document('users', username, {'password': password, 'email': email, 'lastindex': lastindex})
            print(username+"'s account has been created successfully!")
            return True

    def login(self, username: str, password: str, silent:bool=True) -> bool:
        """
        Authenticate a user based on username and password.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.
            silent (bool): (Optional) Tells the login to execute with or without console message

        Returns:
            bool: True if login is successful, False otherwise.
        """
        user_data = self._get_user_data(username)
        if user_data and user_data.get('password') == password:
            self.current_user = username
            if silent is False:
                print("Login successful!")
            return True
        else:
            if silent is False:
                print("Invalid username or password.")
            return False

    def logout(self) -> bool:
        """
        Log out the current user.

        Returns:
            bool: True if logout is successful, False otherwise.
        """

        if self.current_user:
            print(f"User '{self.current_user}' has logged out.")
            self.current_user = None
            return True
        else:
            print("No user is currently logged in.")
            return False

    def add_transaction(self, 
                        serial_no: int, 
                        date: str|datetime, 
                        name: str, 
                        stock_symbol: str, 
                        transaction_type: str, 
                        count: int, 
                        price: float, 
                        total_amount: float= 0.0) -> bool:
        """
        Add a new stock transaction for the current user.

        Args:
            serial_no (int): Serial number for the transaction.
            date (str|datetime): Date of the transaction.
            name (str): Name of the stock.
            stock_symbol (str): Stock symbol.
            transaction_type (str): Either "buy" or "sell".
            count (int): Number of shares.
            price (float): Price per share.
            total_amount (float): (Not needed anymore) Total transaction amount.

        Returns:
            bool: True if the transaction was added successfully, False otherwise.
        """
        total_amount=count*price
        
        if not self.current_user:
            print("Please login to add a transaction.")
            return False

        fdate = date
        
        if(type(date)==str):
            # Convert the string to a datetime object
            date_object = datetime.strptime(date, "%d-%m-%Y")

            # Format the datetime object to match the previous example's format
            formatted_date = date_object.strftime("%d %B %Y at %H:%M:%S UTC%z")
            fdate = datetime.strptime(formatted_date, "%d %B %Y at %H:%M:%S %Z")
        
        transaction_data = {
            'Sl_No': serial_no,
            'Date': fdate,
            'Share': name,
            'Symbol': stock_symbol,
            'Transaction': transaction_type,
            'Count': count,
            'Price': price,
            'Total_Amount': total_amount
        }
        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions_ref.add(transaction_data)
        print("Transaction added successfully!")
        
        return True

    def delete_transaction(self, serial_no: int) -> bool:
        """
        Delete a stock transaction by its serial number for the current user.

        Args:
            serial_no (int): The serial number of the transaction to delete.

        Returns:
            bool: True if the transaction was deleted successfully, False otherwise.
        """
        if not self.current_user:
            print("Please login to delete a transaction.")
            return False

        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.where('Sl_No', '==', serial_no).stream()

        deleted = False
        for transaction in transactions:
            transaction.reference.delete()
            print(f"Transaction with serial number {serial_no} deleted.")
            deleted = True

        if not deleted:
            print(f"No transaction found with serial number {serial_no}.")
            
        return deleted

    def modify_transaction(self, serial_no: int, 
                           date: Optional[str|datetime] = None, 
                           name: Optional[str] = None, 
                           stock_symbol: Optional[str] = None, 
                           transaction_type: Optional[str] = None, 
                           count: Optional[int] = None, 
                           price: Optional[float] = None) -> bool:
        
        """
        Modify an existing transaction identified by its serial number.

        Args:
            serial_no (int): Serial number of the transaction to modify.
            date (Optional[str|datetime]): New date of the transaction (if provided).
            name (Optional[str]): New name of the stock (if provided).
            stock_symbol (Optional[str]): New stock symbol (if provided).
            transaction_type (Optional[str]): New transaction type (if provided).
            count (Optional[int]): New number of shares (if provided).
            price (Optional[float]): New price per share (if provided).

        Returns:
            bool: True if the transaction was updated successfully, False otherwise.
        """
        if not self.current_user:
            print("Please login to modify a transaction.")
            return False

        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.where('Sl_No', '==', serial_no).stream()

        updated = False
        for transaction in transactions:
            transaction_data = transaction.to_dict()

            # Update provided fields
            if date:
                if isinstance(date, str):
                    date_object = datetime.strptime(date, "%d-%m-%Y")
                    date = datetime.strptime(date_object.strftime("%d %B %Y at %H:%M:%S UTC%z"), "%d %B %Y at %H:%M:%S %Z")
                transaction_data['Date'] = date
            if name:
                transaction_data['Share'] = name
            if stock_symbol:
                transaction_data['Symbol'] = stock_symbol
            if transaction_type:
                transaction_data['Transaction'] = transaction_type.lower()
            if count:
                transaction_data['Count'] = count
            if price:
                transaction_data['Price'] = price

            # Recalculate total amount if count or price changed
            if count or price:
                transaction_data['Total_Amount'] = transaction_data['Count'] * transaction_data['Price']

            # Update the transaction in Firestore
            transaction.reference.update(transaction_data)
            print(f"Transaction with serial number {serial_no} has been updated.")
            updated = True

        if not updated:
            print(f"No transaction found with serial number {serial_no}.")
        
        return updated

    def list_transactions(self) -> Optional[pd.DataFrame]:
        """
        List all stock transactions for the current user.

        Returns:
            Dataframe with the user transactions data or None if no transactions found.
        """
        if not self.current_user:
            print("Please login to view transactions.")
            return None

        try:
            # Convert transactions to a DataFrame
            df = self.transactions_to_dataframe()
            
            # Check if the DataFrame is empty
            if df.empty:
                return None
            print(df)
            return df
        except Exception as e:
            # Log the exception and return an error message
            return None

    def delete_all_transactions(self) -> bool:
        """
        Delete all stock transactions for the current user.

        Returns:
            bool: True if transactions were deleted successfully, False otherwise.
        """
        if not self.current_user:
            print("Please login to delete transactions.")
            return False

        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.stream()

        deleted = False
        for transaction in transactions:
            transaction.reference.delete()
            deleted = True

        if deleted:
            print(f"All transactions for user '{self.current_user}' have been deleted.")
        else:
            print("No transactions found to delete.")

        return deleted

    def _insert_document(self, collection_name, document_id, data):
        """Insert a document into a specified collection."""
        self.db.collection(collection_name).document(document_id).set(data)

    def _get_user_data(self, username):
        """Retrieve user data from the Firestore."""
        doc_ref = self.db.collection('users').document(username)
        return doc_ref.get().to_dict() if doc_ref.get().exists else None
    
    def transactions_to_dataframe(self) -> Optional[pd.DataFrame]:
        """
        Convert the user's transactions into a pandas DataFrame.

        Returns:
            Optional[pd.DataFrame]: DataFrame containing all transactions if successful,
                                    None if no transactions are found or login fails.
        """
       
        # Fetch transactions for the user
        transactions_ref = self.db.collection('users').document(self.current_user).collection('transactions')
        transactions = transactions_ref.stream()

        # Convert transactions to a list of dictionaries
        transaction_list = []
        for transaction in transactions:
            transaction_data = transaction.to_dict()
            transaction_list.append(transaction_data)

        # Check if there are any transactions
        if not transaction_list:
            print("No transactions found for this user.")
            return None

        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(transaction_list)
        
        # Reordering columns to match df
        df = df[['Sl_No', 'Date', 'Share', 'Symbol', 'Transaction', 'Count', 'Price', 'Total_Amount']]

        # Renaming columns to match df
        df.rename(columns={'Sl_No': 'Sl.No.', 'Total_Amount': 'Total Amount'}, inplace=True)

        # Removing the time component from the 'Date' column
        df['Date'] = df['Date'].dt.date

        # Ensuring 'Date' is in datetime format without time zone information (if necessary)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sorting df by 'Sl.No.' in ascending order
        df = df.sort_values(by='Sl.No.').reset_index(drop=True)
        
        # Capitalizing the uncapitalized transaction entries
        df['Transaction'] = df['Transaction'].str.capitalize()

        return df
    
    def add_transactions_from_excel(self, filepath: str) ->None:
        """
        Add transactions from an Excel sheet to a user's Firestore transaction collection.

        Args:
            filepath (str): Path to the Excel file containing transaction data.

        Returns:
            None
        """
        # Check if user is logged in
        if not self.current_user:
            print("Login to add transactions. Transactions not added.")
            return
        
        
        # Load Excel data
        data = pd.ExcelFile(filepath)
        sheet_data = data.parse(data.sheet_names[0])
        
        # Loop through each row and add the transaction
        for _, row in sheet_data.iterrows():
            self.add_transaction(
                serial_no=row['Sl.No.'],
                date=row['Date'],
                name=row['Share'],
                stock_symbol=row['Symbol'],
                transaction_type=row['Transaction'].lower(),
                count=row['Count'],
                price=row['Price'],
                total_amount=row['Total Amount']
            )
        
        print(f"All transactions from {filepath} have been successfully added to {self.current_user}'s account.")
        
    def replace_transaction_history(self, transactions: list[dict]) -> Optional[bool]:
        """
        Deletes the entire transaction history of the logged-in user
        and replaces it with new transactions from a given list.

        Args:
            transactions (list[dict]): List of new transaction dictionaries.
        """
        # Check if the user is logged in
        if not self.current_user:
            print("Please login to perform this action.")
            return None
        
        # Dictionary to store the first occurrence of each stock code
        stock_code_to_name = {}
        
        # Iterate through the list and update names based on the first occurrence
        for record in transactions:
            stock_code = record["Symbol"]
            stock_name = record["Share"]
            
            # If the stock code is seen for the first time, record its name
            if stock_code not in stock_code_to_name:
                stock_code_to_name[stock_code] = stock_name
            else:
                # Standardize the name to match the first occurrence
                record["Share"] = stock_code_to_name[stock_code]
            
        df=self.transactions_to_dataframe()
        
        try:    
            # Delete all existing transactions
            print("Deleting existing transaction history...")
            self.delete_all_transactions()
            
            # Add new transactions from the provided list
            print("Adding new transaction history...")
            for transaction in transactions:
                self.add_transaction(
                    serial_no=transaction['Sl_No'],
                    date=transaction['Date'],
                    name=transaction['Share'],
                    stock_symbol=transaction['Symbol'],
                    transaction_type=transaction['Transaction'].lower(),
                    count=transaction['Count'],
                    price=transaction['Price'],
                    total_amount=transaction['Total_Amount']
                )
            
            print("Transaction history replaced successfully!")
        except:
            for _, row in df.iterrows():
                self.add_transaction(
                    serial_no=row['Sl_No'],
                    date=row['Date'],
                    name=row['Share'],
                    stock_symbol=row['Symbol'],
                    transaction_type=row['Transaction'].lower(),
                    count=row['Count'],
                    price=row['Price'],
                    total_amount=row['Total_Amount']
                )
            return False

        return True


def main():
    """Main function to interact with the StockTransactionManager."""
    
    manager = StockTransactionManager()
    
    while True:
        print("\nWelcome to the Stock Transaction Manager")
        print("1. Create Account")
        print("2. Login")
        print("3. Add Transaction")
        print("4. Delete Transaction")
        print("5. List Transactions")
        print("6. Logout")
        print("7. Import Portfolio from Excel")
        print("8. Modify Transactions")
        print("9. Exit")

        choice = input("Choose an option: ")
        
        if choice == '1':
            username = input("Enter a new username: ")
            password = input("Enter a new password: ")
            manager.create_account(username, password)

        elif choice == '2':
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            manager.login(username, password,silent=False)

        elif choice == '3':
            if manager.current_user:
                serial_no = int(input("Enter serial number: "))
                date = input("Enter date (DD-MM-YYYY): ")
                name = input("Enter stock name: ")
                stock_symbol = input("Enter stock symbol: ")
                transaction_type = input("Enter transaction type (buy/sell): ").lower()
                count = int(input("Enter number of shares: "))
                price = float(input("Enter price per share: "))
                total_amount = count * price
                manager.add_transaction(serial_no, date, name, stock_symbol, transaction_type, count, price, total_amount)
            else:
                print("Please login to add a transaction.")

        elif choice == '4':
            if manager.current_user:
                serial_no = int(input("Enter serial number of transaction to delete: "))
                manager.delete_transaction(serial_no)
            else:
                print("Please login to delete a transaction.")

        elif choice == '5':
            manager.list_transactions()

        elif choice == '6':
            manager.logout()
            
        elif choice == '7':
            manager.add_transactions_from_excel("DummyTransactions.xlsx")
        
        elif choice == '8':
            if manager.current_user:
                serial_no = int(input("Enter the serial number of the transaction to modify: "))
                print("Leave fields blank if you don't want to update them.")

                date = input("Enter new date (DD-MM-YYYY) or press Enter to skip: ").strip()
                date = date if date else None
                
                name = input("Enter new stock name or press Enter to skip: ").strip()
                name = name if name else None
                
                stock_symbol = input("Enter new stock symbol or press Enter to skip: ").strip()
                stock_symbol = stock_symbol if stock_symbol else None
                
                transaction_type = input("Enter new transaction type (buy/sell) or press Enter to skip: ").strip()
                transaction_type = transaction_type.lower() if transaction_type else None
                
                count = input("Enter new number of shares or press Enter to skip: ").strip()
                count = int(count) if count else None
                
                price = input("Enter new price per share or press Enter to skip: ").strip()
                price = float(price) if price else None

                manager.modify_transaction(serial_no, date, name, stock_symbol, transaction_type, count, price)
            else:
                print("Please login to modify a transaction.")
        
        elif choice == '9':
            print("Exiting program...")
            break
        
        elif choice == 'd101':
            manager.delete_all_transactions()

        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
