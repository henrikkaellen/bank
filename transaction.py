import datetime
from decimal import *

getcontext().rounding = ROUND_HALF_UP

from sqlalchemy import Column, Integer, ForeignKey, DATE, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Transaction(Base):
    
    __tablename__ = "transaction"
    
    _id = Column(Integer, primary_key=True)
    _account_id = Column(Integer, ForeignKey("account._id"))

    _creation_date = Column(DATE)
    _amount = Column(Float(asdecimal=True))
    _interest_flag = Column(Integer)

    def __init__(self, amount, date = datetime.date.today(), i_flag = 0):
        self._creation_date = date
        self._amount = Decimal(amount)
        self._interest_flag = i_flag
    
    def __lt__(self, other):
        return self._creation_date < other._creation_date
    
    def check_flag_and_date(self, date):
        """check if the interest has already been applied for this month"""
        if self._creation_date == date and self._interest_flag == 1:
            return True
        
        return False
    
    def print_transaction(self):
        """Print the transaction for "list
        transactions"."""
        print(str(self._creation_date) + f", ${Decimal(self._amount):,.2f}")
    
    def __str__(self):
        """Print the transaction for "list
        transactions"."""
        return (str(self._creation_date) + f", ${Decimal(self._amount):,.2f}")
    
    def get_amt(self):
        """Return the transaction amount"""
        return self._amount

    def check_day_limit(self, date):
        """
        Check if date is the same day to add 1 to the day_counter.
        """
        if self._creation_date == date and self._interest_flag == 0:
            return True
        else:
            return False
    
    def check_month_limit(self, date):
        """
        Check if date is the same month to add 1 to the month_counter.
        """
        if self._creation_date.month == date.month and self._creation_date.year == date.year and self._interest_flag == 0:
            return True
        else:
            return False