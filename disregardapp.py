import os
import urllib.parse
import datetime

from flask import Flask, session, flash, jsonify, redirect, render_template, request
from flask_session.__init__ import Session #from stackoverflow
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

###
# INDEX
###

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
     # Query stocks database for stocks owned by this user based on session id, group by symbol so you get summaries
    rows = db.execute("SELECT symbol, name, price, SUM(shares) FROM stocks WHERE owner = :owner GROUP BY symbol", owner=session["user_id"])

    # start a variable to keep track of total value of stocks owned
    stocksTotal = 0

    for row in rows:
        #lookup the symbol and store in variable mydictionary so you can access price
        mydictionary = lookup(row["symbol"])
        rowTotal = float(row["SUM(shares)"] * mydictionary["price"])
        row["total"] = usd(rowTotal)
        stocksTotal = stocksTotal + rowTotal
        stocksTotalUsd = usd(stocksTotal)
        row["price"] = usd(mydictionary["price"])

    cashAvailable = db.execute('SELECT cash FROM users WHERE id = :id', id=session["user_id"])
    cashAvailableValue = usd(cashAvailable[0]["cash"])

    stocksTotalUsd = usd(stocksTotal + cashAvailable[0]["cash"])


    return render_template("index.html", data=rows, cash=cashAvailableValue, stocksTotal = stocksTotalUsd)

###
# BUY
###

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
     # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must enter a symbol", 403)

        elif not shares:
            return apology("must enter a number", 403)

        else:
            sharesInt = int(shares)
            thisUserId=session["user_id"]
            mydictionary = lookup(symbol)


            if sharesInt < 1:
                return apology("Must enter a positive integer", 403)

            cashAvailable = db.execute('SELECT cash FROM users WHERE id = :id', id=thisUserId)
            cashAvailableValue = cashAvailable[0]["cash"]

            if cashAvailableValue >= sharesInt*mydictionary["price"]:
                db.execute("INSERT INTO stocks (owner, symbol, name, shares, price, buy, date) VALUES (:owner, :symbol, :name, :shares, :price, :buy, :date)", owner=session["user_id"], symbol=symbol, name=mydictionary["name"], shares=shares, price=mydictionary["price"], buy="true", date=datetime.datetime.now())
                #update user's cash amount in database
                db.execute("UPDATE users SET cash = :updatedCash WHERE id = :thisUser", updatedCash = float(cashAvailableValue) - float(shares) * mydictionary["price"], thisUser = session["user_id"])

                # Redirect user to home page
                return redirect("/")
            else:
                return apology("Insufficient funds to cover this transaction", 403)


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


###
# HISTORY
###

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
     # Query stocks database for stocks owned by this user based on session id
    rows = db.execute("SELECT * FROM stocks WHERE owner = :owner", owner=session['user_id'])

    for row in rows:
        row["price"] = usd(row["price"])

    return render_template("history.html", data=rows)


###
# LOG IN
###

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username");
        password = request.form.get("password");


        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        thisUserId = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


###
# LOG OUT
###

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


###
# QUOTE
###

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")

        mydictionary = lookup(symbol)

        return render_template("quote-result.html", name=mydictionary["name"], price=mydictionary["price"], symbol=mydictionary["symbol"])


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


###
# REGISTER
###

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        session.clear()

        username = request.form.get("username")
        password = request.form.get("password")
        passwordConfirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must enter a username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must enter a password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Check if username already exists
        if len(rows) >= 1:
            return apology("that username is already in use, please choose a new unique one", 403)

        # Check if the two password fields match
        if password != passwordConfirmation:
            return apology("passwords do not match each other - try again")

        # Insert into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username=username, password=generate_password_hash(password))

        # Remember which user has logged in
        rows2 = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        session["user_id"] = rows2[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


###
# SELL
###

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        if not symbol:
            return apology("must enter a symbol", 403)

        elif not shares:
            return apology("must enter a number", 403)

        else:
            sharesInt = int(shares)
            thisUserId=session["user_id"]
            mydictionary = lookup(symbol)


            if sharesInt < 1:
                return apology("Must enter a positive integer", 403)

            cashAvailable = db.execute('SELECT cash FROM users WHERE id = :id', id=thisUserId)
            cashAvailableValue = cashAvailable[0]["cash"]

            rows = db.execute("SELECT SUM(shares) FROM stocks WHERE owner = :owner AND symbol = :symbol", owner=session["user_id"], symbol=symbol)

            sharesTotal = rows[0]["SUM(shares)"]

            # if they have enough shares to cover the sale
            if sharesTotal >= sharesInt:
                # insert into stocks database as negative number of shares, makes updating the totals easier, can denote sale in history page with negative number
                db.execute("INSERT INTO stocks (owner, symbol, name, shares, price, buy, date) VALUES (:owner, :symbol, :name, :shares, :price, :buy, :date)", owner=session["user_id"], symbol=symbol, name=mydictionary["name"], shares=-1 * sharesInt, price=mydictionary["price"], buy="false", date=datetime.datetime.now())

                # also update user's cash amount in database
                db.execute("UPDATE users SET cash = :updatedCash WHERE id = :thisUser", updatedCash = float(cashAvailableValue) + float(shares) * mydictionary["price"], thisUser = session["user_id"])

                # Redirect user to home page
                return redirect("/")
            else:
                return apology("This number exceeds the amount of shares you own", 403)


    # User reached route via GET (as by clicking a link or via redirect)
    else:

        rows = db.execute("SELECT symbol FROM stocks WHERE owner = :owner GROUP BY symbol", owner=session['user_id'])
        return render_template("sell.html", rows = rows)


###
# ADD CASH
###

@app.route("/addCash", methods=["GET", "POST"])
@login_required
def addCash():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        addCashAmount = request.form.get("add-cash")
        thisUserId=session["user_id"]

        cashAvailable = db.execute('SELECT cash FROM users WHERE id = :id', id=thisUserId)
        cashAvailableValue = cashAvailable[0]["cash"]

        if float(addCashAmount) > 0:
            db.execute("UPDATE users SET cash = :updatedCash WHERE id = :thisUser", updatedCash = float(cashAvailableValue) + float(addCashAmount), thisUser = thisUserId)
        else:
            return apology("Please enter a positive amount", 403)

        # Redirect user to home page
        return redirect("/")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add-cash.html")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
