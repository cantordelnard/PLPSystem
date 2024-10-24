from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from .db import sign_up, validate_login

auth = Blueprint('auth', __name__)


#<!-- =============== LOGIN ================ -->
@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = validate_login(username, password)
        if user:
            session["user_id"] = user["UserID"]  # Store user ID in session
            if user["RoleID"] == 1:
                flash("Login Succesfully!")
                return redirect(url_for("views.admin"))
            elif user["RoleID"] == 2:
                flash("Login Succesfully!")
                return redirect(url_for("views.professors"))
            elif user["RoleID"] == 3:
                flash("Login Succesfully!")
                return redirect(url_for("views.studentsHome"))
            else:
                flash("Invalid user role.")
                return redirect(url_for("auth.login"))
        else:
            flash("Invalid Username or Password.")
            return redirect(url_for("auth.login"))
    return render_template("login.html")


#<!-- =============== LOGOUT ================ -->
@auth.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role_id = request.form["role_id"]  # Make sure to add a field for role ID in the signup form
        if sign_up(role_id, username, password):
            flash("Signup Successful! You can now log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Signup failed. Please try again.", "danger")
            return redirect(url_for("auth.signup"))
    return render_template("signup.html")
