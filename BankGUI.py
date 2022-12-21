import tkinter as tk
from tkinter import messagebox
from bank import Bank
import logging
from transaction import Base
from decimal import *
import datetime
from account import OverdrawError
from account import TransactionLimitError
from account import TransactionSequenceError
from tkcalendar import DateEntry
import sys

import sqlalchemy
from sqlalchemy.orm.session import sessionmaker

class BankGUI:
    """Display a menu and respond to choices when run"""

    def __init__(self):
        self._session = Session()

        self._bank = self._session.query(Bank).first()
        logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        logging.debug("Loaded from bank.db")
        if not self._bank:
            self._bank = Bank()
            self._session.add(self._bank)
            self._session.commit()
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Saved to bank.db")

        self._window = tk.Tk()
        self._window.title("My Bank")

        def handle_exception(exception, value, traceback):
            messagebox.showwarning(message="Sorry! Something unexpected happened. If this problem persists please contact our support team for assistance.")
            logging.error(f"{exception.__name__}: {repr(value)}")
            sys.exit(1)

        self._window.report_callback_exception = handle_exception

        self._bank = Bank()
        self._options_frame = tk.Frame(self._window)

        tk.Button(self._options_frame,
                  text="open account",
                  command=self._open_account).grid(row=1, column=3)
        
        tk.Button(self._options_frame,
                  text="add transaction",
                  command=self._add_transaction).grid(row=1, column=4)

        tk.Button(self._options_frame,
                  text="interest and fees",
                  command=self._interest_and_fees).grid(row=1, column=5)
        
        self._account_frame = tk.Frame(self._window)
        self._transactions_frame = tk.Frame(self._window)
        self._options_frame.grid(row=0, column=1, columnspan=2)
        self._search_frame = tk.Frame(self._window)
        self._search_frame.grid(row=1, column=1)
        self._account_frame.grid(row=2, column=1)
        self._transactions_frame.grid(row = 2, column = 2)

        self._list_box = None
        self._select_account = None
        self._input_flag = 1

        self.var=tk.IntVar()
        
        self._window.mainloop()
    

    def _validate(self, event, field):
        """Validates the input to a"""
        input = field.get()
        try:
            Decimal(input)
            field.config(highlightbackground="green")
            self._input_flag = 0
        except InvalidOperation:
            field.config(highlightbackground="red")
            self._input_flag = 1

    def _open_account(self):
        """Opens a new savings or checking account"""
        def add_callback():
            if self._input_flag == 1:
                messagebox.showwarning(message="Please try again with a valid dollar amount.")
                return

            account = self._bank.new_account(variable.get(), self._session)
            try:
                account.add_transaction(Decimal(e1.get()), datetime.date.today(), self._session)
            except OverdrawError:
                messagebox.showwarning(message="This transaction could not be completed due to an insufficient account balance.")

            e1.destroy()
            b.destroy()
            l1.destroy()
            c.destroy()

            self._display_accounts()

            self._session.commit()
            logging.basicConfig(filename= 'bank.log', level = logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            logging.debug("Saved to bank.db")
        


        l1 = tk.Label(self._search_frame, text="Initial deposit:")
        l1.grid(row=5, column=1)
        e1 = tk.Entry(self._search_frame)
        e1.bind("<KeyRelease>", lambda x, y=e1: self._validate(x, y))
        e1.grid(row=6, column=1)

        b = tk.Button(self._search_frame, text="Enter", command=add_callback)
        b.grid(row=8, column=2)

        c_list = ["checking", "savings"]
        variable = tk.StringVar(self._window)
        variable.set(c_list[0])

        c = tk.OptionMenu(self._search_frame, variable, *c_list)
        c.grid(row=8, column=1)

    def _display_accounts(self):
        """Displays all accounts in the bank"""
        def callback():
            selected_account = self._bank.find_account(self.var.get())
            self._display_transactions(selected_account)
            self._select_account = selected_account
        

        account_buttons = []
        row = 0
        for account in self._bank.all_accounts():
            account_buttons.append(tk.Radiobutton(self._account_frame, text=account, variable=self.var, value=account.get_id(), command=callback).grid(row=row, column=1))
            row += 1
    
    def _display_transactions(self, account):
        """Displays the transactions of an account"""
        if self._list_box:
            self._list_box.delete(0,tk.END)
        
        else:
            self._list_box = tk.Listbox(self._transactions_frame)
            
        row = 1
        sorted_transaction_list = account.sort_transactions()
        for transaction in sorted_transaction_list:
            self._list_box.insert(row, transaction)

            #use get amount to change color of transaction
            if transaction.get_amt() > 0:
                self._list_box.itemconfig(row-1, {'fg':'green'})
            else:
                self._list_box.itemconfig(row-1, {'fg':'red'})
            
            row +=1
        
        self._list_box.pack()

    def _add_transaction(self):
        """Adds a new transaction to an account"""
        def add_callback():
            if self._input_flag == 1:
                messagebox.showwarning(message="Please try again with a valid dollar amount.")
                return
            try:
                self._select_account.add_transaction(Decimal(e1.get()), cal.get_date(), self._session)
                self._display_accounts()
                self._display_transactions(self._select_account)
                e1.destroy()
                cal.destroy()
                b.destroy()
                l1.destroy()
            except AttributeError: 
                messagebox.showwarning(message="This command requires that you first select an account.")
            except OverdrawError:
                messagebox.showwarning(message="This transaction could not be completed due to an insufficient account balance.")
            except TransactionLimitError:
                messagebox.showwarning(message="This transaction could not be completed because the account has reached a transaction limit.")
            except TransactionSequenceError as e:
                messagebox.showwarning(message="New transactions must be from " + str(e.latest_date) +  " onward.")

        l1 = tk.Label(self._options_frame, text="Amount:")
        l1.grid(row=5, column=3)
        e1 = tk.Entry(self._options_frame)
        e1.bind("<KeyRelease>", lambda x, y=e1: self._validate(x, y))
        e1.grid(row=5, column=4)


        cal = DateEntry(self._options_frame,selectmode='day',year=2023,month=1,day=1)
        cal.grid(row=6, column = 4)

        b = tk.Button(self._options_frame, text="Enter", command=add_callback)
        b.grid(row=6, column=5)
        
    def _interest_and_fees(self):
        """Assesses the interest and fees to an account"""
        try:
            self._select_account.assess_interest_and_fees(self._session)
            self._display_accounts()
            self._display_transactions(self._select_account)
        except AttributeError: 
            messagebox.showwarning(message="This command requires that you first select an account.")
        except TransactionSequenceError as e:
            messagebox.showwarning(message="Cannot apply interest and fees again in the month of " + str(e.latest_date.strftime("%B")) + ".")
        

if __name__ == "__main__":
    engine = sqlalchemy.create_engine(f"sqlite:///bank.db")
    Base.metadata.create_all(engine)

    Session = sessionmaker()
    Session.configure(bind=engine)

    BankGUI()