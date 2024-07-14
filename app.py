# Personal Finance Tracker

import numpy as np
from enum import Enum, auto
from datetime import datetime
import redis
import json
import uuid

class ExpenseType(Enum):
    Groceries = 1
    Transport = 2
    Housing = 3
    Utility = 4
    Entertainment = 5
    Insurance = 6
    HealthCare = 7
    Miscellaneous = auto()

class IncomeType(Enum):
    Salary = 1
    BusinessIncome = 2
    InvestmentIncome = 3
    RentalIncome = 4
    Pension = 5
    Miscellaneous = auto()

class Expense:
    m_expenseType = ExpenseType.Miscellaneous
    m_amount = 0
    m_date = datetime.today()

    def __init__(self, p_expenseType, p_amount, p_date) -> None:
        self.m_expenseType = p_expenseType
        self.m_amount = p_amount
        self.m_date = p_date

    # Deserialize the object
    def Deserialize(p_objAsString):
        data = json.loads(p_objAsString)
        return Expense(**data)

class Income:
    m_incomeType = ExpenseType.Miscellaneous
    m_amount = 0
    m_date = datetime.today()

    def __init__(self, p_incomeType, p_amount, p_date) -> None:
        self.m_incomeType = p_incomeType
        self.m_amount = p_amount
        self.m_date = p_date

    # Deserialize the object
    def Deserialize(p_objAsString):
        data = json.loads(p_objAsString)
        return Income(**data)

# Create a connection to the Redis server running using: docker run --name redis -d -p 6379:6379 redis
AuthDB = redis.Redis(host='localhost', port=6379, db=0)
UserInfoDB = redis.Redis(host='localhost', port=6379, db=1)

class User:
    m_userName = ""
    m_password = ""
    m_userId = uuid.UUID(int=0)

    def __init__(self, p_userName="", p_password="", p_userId="") -> None:
        self.m_userName = p_userName
        self.m_password = p_password
        self.m_userId = p_userId

    # Serialize the object
    def Serialize(self):
        return json.dumps({
            'userName': self.m_userName,
            'password': self.m_password,
            'userId': str(self.m_userId)  # Convert UUID to string for JSON
        })

    # Deserialize the object
    def Deserialize(self, p_objAsString):
        data = json.loads(p_objAsString)
        self.m_userName=data['userName']
        self.m_password=data['password']
        self.m_userId=uuid.UUID(data['userId'])  # Convert back to UUID - Pyhton doesn't handle implicit conversion

class ErrorCode(Enum):
    OK = auto()
    FAIL = auto()
    USERNAME_ALREADY_EXISTS = auto()
    USERNAME_DOES_NOT_EXIST = auto()
    WEAK_PASSWORD = auto()

class Auth:
    def SignUp(p_userName, p_password):
        if AuthDB.exists(p_userName):
            return ErrorCode.USERNAME_ALREADY_EXISTS
        if p_password is None:
            return ErrorCode.WEAK_PASSWORD
        AuthDB.set(p_userName, p_password)
        
        l_user = User(p_userName, p_password, uuid.uuid4())
        result = UserInfoDB.hset(p_userName, mapping=json.loads(User.Serialize(l_user)))
        return ErrorCode.OK

    def Login(p_userName, p_password):
        l_password = AuthDB.get(p_userName)
        if l_password is not None and (l_password.decode('utf-8') == p_password):
            return ErrorCode.OK
        else:
            return ErrorCode.FAIL
    
    def DeleteAccount(p_userName):
        if AuthDB.exists(p_userName) == False:
            return ErrorCode.USERNAME_DOES_NOT_EXIST
        AuthDB.delete(p_userName)
        if UserInfoDB.hkeys(p_userName):
            UserInfoDB.hdel(p_userName, *UserInfoDB.hkeys(p_userName))
        return ErrorCode.OK
    
    def GetUser(p_userName, p_password, p_user):
        if Auth.Login(p_userName, p_password) == ErrorCode.OK:
            l_userInfo = UserInfoDB.hgetall(p_userName)
            # Convert dictionary of byte strings to a regular dictionary
            l_userInfoDecoded = {ky.decode('utf-8'): val.decode('utf-8') for ky, val in l_userInfo.items()}
            p_user.Deserialize(json.dumps(l_userInfoDecoded))
            return ErrorCode.OK
        return ErrorCode.FAIL


# Clear the current database
AuthDB.flushdb()
UserInfoDB.flushdb()

print(Auth.Login("Rushil", "1234"))
print(Auth.SignUp("Rushil", "1234"))
print(Auth.Login("Rushil", "1234"))

l_user = User()
print(Auth.GetUser("Rushil", "1234", l_user))
print(l_user.Serialize())

print(Auth.DeleteAccount("Rushil"))
print(Auth.Login("Rushil", "1234"))

