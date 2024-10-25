import os
from flask import Blueprint, current_app, render_template, session, redirect, url_for, flash, request, jsonify
import mysql.connector
from .db import add_class, add_or_update_academic_requirement, add_professoradvisory, add_program, add_schoolyear, add_specialization, add_subject, archive_schoolyear_data, connect_to_database, fetch_academic_interventions, fetch_alerts, fetch_behavioral_interventions, fetch_prediction, fetch_socioeconomic_interventions, fetch_student_id, get_academic_interventions, get_admin_count, get_archived_schoolyears, get_average_percentage, get_class_by_id, get_classes_list, get_existing_comment, get_existing_link, get_professor_classes_subjects, get_professor_count, get_professor_id_by_user_id, get_professor_list, get_professoradvisory_by_id, get_professoradvisory_list, get_program_by_id, get_schoolyear_by_id, get_schoolyear_list, get_semesters_list, get_specialization_by_id, get_student_count, get_student_grades, get_student_grades_archive, get_student_info, get_admin_info, get_professors_info, get_student_info_explore, get_student_predictions, get_student_predictions_by_professor_and_subject, get_students_by_class, get_subject_by_id, get_subject_count, get_subject_details, get_subject_list, insert_admins, insert_classes, insert_prof, insert_professoradvisory, insert_schoolyears, insert_students, insert_user, get_program_list, get_specialization_list, get_class_list, get_year_level_list, insert_users, perform_intervention_based_on_factor, update_class_db, update_professoradvisory_db, update_program_db, update_schoolyear, update_specialization_db, update_subject_db
import logging
import pandas as pd
from sklearn.pipeline import Pipeline
from .models import model
from werkzeug.utils import secure_filename
import bcrypt

logging.basicConfig(level=logging.DEBUG)
views = Blueprint('views', __name__)

def validate_excel_maintenance(df_schoolyear, df_classes, df_prof_advisory):
    required_schoolyear_columns = ['Year']
    required_classes_columns = ['ClassName', 'SchoolYearID']
    required_prof_advisory_columns = ['ProfessorID', 'ClassID', 'SubjectID', 'SemesterID']

    # Validate SCHOOLYEAR sheet
    for col in required_schoolyear_columns:
        if col not in df_schoolyear.columns:
            raise ValueError(f"Missing column {col} in SCHOOLYEAR sheet.")
        if df_schoolyear[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in SCHOOLYEAR sheet.")

    # Validate CLASSES sheet
    for col in required_classes_columns:
        if col not in df_classes.columns:
            raise ValueError(f"Missing column {col} in CLASSES sheet.")
        if df_classes[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in CLASSES sheet.")

    # Validate PROFESSOR ADVISORY sheet
    for col in required_prof_advisory_columns:
        if col not in df_prof_advisory.columns:
            raise ValueError(f"Missing column {col} in PROFESSOR ADVISORY sheet.")
        if df_prof_advisory[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in PROFESSOR ADVISORY sheet.")

@views.route('/bulk_upload_schoolyear', methods=['POST'])
def bulk_upload_schoolyear():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and file.filename.endswith(('.xls', '.xlsx')):
        try:
            # Read the Excel file into a DataFrame
            xl = pd.ExcelFile(file)

            # Load different sheets
            df_schoolyear = xl.parse('SCHOOLYEAR')
            df_classes = xl.parse('CLASSES')
            df_prof_advisory = xl.parse('PROFESSORADVISORY')

            # Validate the content of the sheets
            validate_excel_maintenance(df_schoolyear, df_classes, df_prof_advisory)

            # Check for duplicates in each table
            duplicates_schoolyear = check_duplicates_schoolyear(df_schoolyear)
            duplicates_classes = check_duplicates_classes(df_classes)
            duplicates_prof_advisory = check_duplicates_prof_advisory(df_prof_advisory)

            # Combine duplicates into one list
            duplicates = duplicates_schoolyear + duplicates_classes + duplicates_prof_advisory

            # If there are duplicates, show the popup modal
            if duplicates:
                return render_template('adminUpload.html', show_popup=True, duplicates=duplicates)

            # If no duplicates, insert data into respective tables
            insert_schoolyears(df_schoolyear)
            insert_classes(df_classes)
            insert_professoradvisory(df_prof_advisory)

            # Flash success message
            flash('Bulk upload for Maintenance was successful!')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            return redirect(request.url)

    return redirect(url_for('views.adminUpload'))

def check_duplicates_schoolyear(df_schoolyear):
    conn = connect_to_database()
    cursor = conn.cursor()

    duplicate_entries = []
    for index, row in df_schoolyear.iterrows():
        cursor.execute("SELECT SchoolYearID FROM schoolyear WHERE Year = %s", (row['Year'],))
        duplicate = cursor.fetchone()
        if duplicate:
            duplicate_entries.append({
                'entry_type': 'School Year',
                'identifier': duplicate[0],  # This should be SchoolYearID
                'additional_info': ''
            })

    cursor.close()
    conn.close()
    return duplicate_entries

def check_duplicates_classes(df_classes):
    conn = connect_to_database()
    cursor = conn.cursor()

    duplicate_entries = []
    for index, row in df_classes.iterrows():
        cursor.execute("SELECT ClassID FROM classes WHERE ClassName = %s AND SchoolYearID = %s", 
                       (row['ClassName'], row['SchoolYearID']))
        duplicate = cursor.fetchone()
        if duplicate:
            duplicate_entries.append({
                'entry_type': 'Class',
                'identifier': duplicate[0],  # This should be ClassID
                'additional_info': ''
            })

    cursor.close()
    conn.close()
    return duplicate_entries

def check_duplicates_prof_advisory(df_prof_advisory):
    conn = connect_to_database()
    cursor = conn.cursor()

    duplicate_entries = []
    for index, row in df_prof_advisory.iterrows():
        cursor.execute("SELECT AdvisoryID FROM professoradvisory WHERE ProfessorID = %s AND ClassID = %s", 
                       (row['ProfessorID'], row['ClassID']))
        duplicate = cursor.fetchone()
        if duplicate:
            duplicate_entries.append({
                'entry_type': 'Professor Advisory',
                'identifier': duplicate[0],  # This should be AdvisoryID
                'additional_info': ''
            })

    cursor.close()
    conn.close()
    return duplicate_entries

def validate_excel_content(df_users, df_admins, df_prof, df_students):
    required_user_columns = ['UserID', 'Username', 'Password', 'RoleID']
    required_admin_columns = ['UserID', 'FirstName', 'LastName', 'Email']
    required_prof_columns = ['UserID', 'FirstName', 'LastName', 'Email', 'ProgramID']
    required_student_columns = ['UserID', 'FirstName', 'LastName', 'Email']

    # Validate USERS sheet
    for col in required_user_columns:
        if col not in df_users.columns:
            raise ValueError(f"Missing column {col} in USERS sheet.")
        if df_users[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in USERS sheet.")

    # Validate ADMINS sheet
    for col in required_admin_columns:
        if col not in df_admins.columns:
            raise ValueError(f"Missing column {col} in ADMINS sheet.")
        if df_admins[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in ADMINS sheet.")

    # Validate PROFESSORS sheet
    for col in required_prof_columns:
        if col not in df_prof.columns:
            raise ValueError(f"Missing column {col} in PROFESSORS sheet.")
        if df_prof[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in PROFESSORS sheet.")

    # Validate STUDENTS sheet
    for col in required_student_columns:
        if col not in df_students.columns:
            raise ValueError(f"Missing column {col} in STUDENTS sheet.")
        if df_students[col].isnull().any():
            raise ValueError(f"Null values found in {col} column in STUDENTS sheet.")
        
@views.route('/bulk_upload', methods=['POST'])
def bulk_upload():
    file = request.files['file']
    if not file:
        flash('No file selected')
        return redirect(url_for('views.adminUpload'))

    try:
        xl = pd.ExcelFile(file)

        # Load Users and other sheets
        df_users = xl.parse('USERS')
        df_admins = xl.parse('ADMINS')
        df_prof = xl.parse('PROFESSORS')
        df_students = xl.parse('STUDENTS')

        # Validate the content of the sheets
        validate_excel_content(df_users, df_admins, df_prof, df_students)

        # Check for duplicates
        duplicates = check_duplicates_in_db(df_users)
        print(f"Found duplicates: {duplicates}")  # Debugging line
        if duplicates:
            # Pass UserID and Username of duplicates to the custom popup
            custom_duplicates = [{'UserID': dup['UserID'], 'Username': dup['Username']} for dup in duplicates]
            return render_template('adminUpload.html', show_custom_popup=True, custom_duplicates=custom_duplicates)

        # Proceed with database insertion if no duplicates
        insert_users(df_users)
        insert_admins(df_admins)
        insert_prof(df_prof)
        insert_students(df_students)

        flash('Bulk upload for Users was Successful!')
    except Exception as e:
        flash(f'An error occurred: {str(e)}')

    return redirect(url_for('views.adminUpload'))

def check_duplicates_in_db(df_users):
    conn = connect_to_database()
    cursor = conn.cursor()

    duplicate_entries = []
    for index, row in df_users.iterrows():
        cursor.execute("SELECT UserID, Username FROM users WHERE UserID = %s", (row['UserID'],))
        duplicate = cursor.fetchone()
        if duplicate:
            duplicate_entries.append({'UserID': duplicate[0], 'Username': duplicate[1]})

    cursor.close()
    conn.close()
    return duplicate_entries


#<!-- =============== BASE TEMPLATE ================ -->
@views.route('/base')
def base():
    return render_template("base.html")


#<!-- =============== BASE TEMPLATE ================ -->
@views.route('/studentsBehavioral', methods=['GET', 'POST'])
def studentBehavioral():
    if "user_id" not in session:
        flash('User is not logged in.')
        return redirect(url_for('auth.login'))

    user_id = session["user_id"]
    student_info = get_student_info(user_id)

    if not student_info:
        flash('Student information not found.')
        return redirect(url_for('views.studentBehavioral'))

    student_id = student_info['StudentID']

    # Fetch prediction information
    prediction_info = fetch_prediction(student_id)  # Assuming this function is defined

    if request.method == 'POST':
        # Retrieve form data
        study_hours = request.form.get('study_hours')
        study_strategies = request.form.get('study_strategies')
        study_schedule = request.form.get('study_schedule')
        attendance_rate = request.form.get('attendance_rate')
        participation = request.form.get('participation')
        time_management = request.form.get('time_management')
        study_deadlines = request.form.get('study_deadlines')
        motivation = request.form.get('motivation')
        engagement = request.form.get('engagement')
        stress_level = request.form.get('stress_level')
        coping_effectiveness = request.form.get('coping_effectiveness')
        average_percentage = request.form.get('average_percentage')

        # Define scoring
        scores = {
            'study_hours': {
                'Less than 5 hours': 1,
                '5-10 hours': 2,
                '11-15 hours': 3,
                '16-20 hours': 4,
                'More than 20 hours': 5
            },
            'study_strategies': {
                'Never': 1,
                'Rarely': 2,
                'Sometimes': 3,
                'Often': 4,
                'Always': 5
            },
            'study_schedule': {
                'Yes': 5,
                'No': 1
            },
            'attendance_rate': {
                'Less than 50%': 1,
                '50-70%': 2,
                '71-90%': 3,
                'More than 90%': 4
            },
            'participation': {
                'Not at all': 1,
                'Slightly': 2,
                'Moderately': 3,
                'Very actively': 4,
                'Extremely actively': 5
            },
            'time_management': {
                'Poor': 1,
                'Fair': 2,
                'Good': 3,
                'Very Good': 4,
                'Excellent': 5
            },
            'study_deadlines': {
                'Never': 1,
                'Rarely': 2,
                'Sometimes': 3,
                'Often': 4,
                'Always': 5
            },
            'motivation': {
                'Not motivated': 1,
                'Slightly motivated': 2,
                'Moderately motivated': 3,
                'Very motivated': 4,
                'Extremely motivated': 5
            },
            'engagement': {
                'Not engaged': 1,
                'Slightly engaged': 2,
                'Moderately engaged': 3,
                'Very engaged': 4,
                'Extremely engaged': 5
            },
            'stress_level': {
                'Never': 5,
                'Rarely': 4,
                'Sometimes': 3,
                'Often': 2,
                'Always': 1
            },
            'coping_effectiveness': {
                'Not effective': 1,
                'Slightly effective': 2,
                'Moderately effective': 3,
                'Very effective': 4,
                'Extremely effective': 5
            },
        }

        # Calculate total score and average
        total_score = 0
        total_questions = 0

        for key, value in scores.items():
            answer = request.form.get(key)
            if answer in value:
                total_score += value[answer]
                total_questions += 1

        # Calculate average percentage
        if total_questions > 0:
            average_percentage = (total_score / (total_questions * 5)) * 100
            # Print average percentage to the terminal
            #print(f'Your Average Score: {average_percentage:.2f}%')  # Display average percentage
        else:
            average_percentage = 0
            #print('No questions answered. Average Score: 0.00%')  # Display message if no questions answered

        # Connect to the database
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                # Insert the data into the behavioral table, including StudentID and average_percentage
                query = '''
                INSERT INTO behavioral (StudentID, StudyHours, StudyStrategies, RegularStudySchedule, AttendanceRate, 
                                        ClassParticipation, TimeManagementRating, StudyDeadlinesFrequency, MotivationLevel, 
                                        EngagementLevel, StressFrequency, CopingEffectiveness, AveragePercentage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                cursor.execute(query, (student_id, study_hours, study_strategies, study_schedule, attendance_rate, 
                                       participation, time_management, study_deadlines, motivation, engagement, 
                                       stress_level, coping_effectiveness, average_percentage))

                # Commit the changes to the database
                connection.commit()

                flash('Survey data submitted successfully!')
                return redirect(url_for('views.studentBehavioral'))

            except Exception as e:
                flash('Incomplete Field Entries!')
                return redirect(url_for('views.studentBehavioral'))

            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed.')
            return redirect(url_for('views.studentBehavioral'))

    # If GET request or any issue, fetch existing data to pre-fill the form
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM behavioral WHERE StudentID = %s', (student_id,))
            existing_data = cursor.fetchone()
            form_data = existing_data if existing_data else {}
        except Exception as e:
            flash(f'Error fetching data: {str(e)}')
            form_data = {}
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed.')
        form_data = {}

    return render_template('studentsBehavioral.html', form_data=form_data, average_percentage=average_percentage if 'average_percentage' in locals() else None, prediction_info=prediction_info)




#<!-- =============== BASE TEMPLATE ================ -->
@views.route('/baseUpdate')
def baseUpdate():
    return render_template("baseUpdate.html")


#<!-- =============== TEST PAGE ================ -->
@views.route('/testPage')
def testPage():
    return render_template("testPage.html")

#<!-- =============== TEST PAGE ================ -->
@views.route('/studentsHome')
def studentsHome():
    if "user_id" in session:
        user_id = session["user_id"]
        
        # Fetch student information
        student_info = get_student_info(user_id)
        
        # Fetch student ID
        student_id = fetch_student_id(user_id)

        if student_info and student_id:
            # Fetch prediction information
            prediction_info = fetch_prediction(student_id)  # You'll need to implement this function
            
            # Fetch alerts for the student
            alerts_info = fetch_alerts(student_id)  # New function to implement
            
            return render_template("studentsHome.html", 
                                   student_info=student_info, 
                                   prediction_info=prediction_info,
                                   alerts_info=alerts_info)  # Pass the alerts info
        else:
            flash("Student information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


#<!-- =============== TEST DASHBOARD ================ -->
@views.route('/')
def home():
    return redirect(url_for('auth.login'))


@views.route('/studentsExplore')
def students_explore():
    if "user_id" in session:
        user_id = session["user_id"]
        
        # Fetch student information
        student_info = get_student_info_explore(user_id)
        
        if student_info:
            student_id = student_info['StudentID']
            
            # Fetch prediction information
            prediction_info = fetch_prediction(student_id)  # Assuming this function is defined
            
            return render_template("studentsExplore.html", student_info=student_info, prediction_info=prediction_info)
        else:
            flash("Student information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))

def generate_comment(input_features, prediction, average_percentage):
    comments = []
    socioeconomic = False
    academic = False
    behavioral = False

    # Check for factors affecting prediction
    if prediction != 1:  # If the prediction is NOT graduating on time
        # Socioeconomic factors
        combined_monthly_income = input_features['mother_monthly_income'] + input_features['father_monthly_income']
        if combined_monthly_income <= 10000:
            comments.append(
                f"Socioeconomic Factor"
            )
            socioeconomic = True

        # Academic factors
        if input_features['average_grade_first_year'] <= 85.49:
            comments.append(
                "Academic Factor"
            )
            academic = True

        # Behavioral comparison
        if average_percentage <= 49.49:
            comments.append(
                f"Behavioral Factor"
            )
            behavioral = True

    # Determine factor_id using pattern matching
    match (socioeconomic, academic, behavioral):
        case (True, True, True):
            factor_id = 7
        case (True, True, False):
            factor_id = 4
        case (True, False, True):
            factor_id = 5
        case (False, True, True):
            factor_id = 6
        case (True, False, False):
            factor_id = 1
        case (False, True, False):
            factor_id = 2
        case (False, False, True):
            factor_id = 3
        case _:
            factor_id = 8  # DEFAULT

    # Combine comments into a single string
    comment_text = "\n".join(comments) if comments else ""

    return comment_text, factor_id  # Returning both comment text and factor ID


@views.route('/predict', methods=['POST'])
def predict():
    data = request.json

    # Convert values to the correct types
    input_features = {
        'age': float(data.get('age', 0)),
        'gender': data.get('gender', 'Unknown'),
        'no_of_siblings': float(data.get('no_of_siblings', 0)),
        'mother_occupation': data.get('mother_occupation', 'None'),
        'mother_monthly_income': float(data.get('mother_monthly_income', 0)),
        'father_occupation': data.get('father_occupation', 'None'),
        'father_monthly_income': float(data.get('father_monthly_income', 0)),
        'average_grade_g12': float(data.get('average_grade_g12', 0.0)),
        'average_grade_first_year': float(data.get('average_grade_first_year', 0.0)),
        'grades_understanding_self': float(data.get('grades_understanding_self', 0.0)),
        'grades_purposive_communication': float(data.get('grades_purposive_communication', 0.0)),
        'grades_art_appreciation': float(data.get('grades_art_appreciation', 0.0)),
        'grades_sts': float(data.get('grades_sts', 0.0)),
        'grades_environmental_science': float(data.get('grades_environmental_science', 0.0)),
        'grades_intermediate_programming': float(data.get('grades_intermediate_programming', 0.0)),
        'grades_discrete_mathematics': float(data.get('grades_discrete_mathematics', 0.0)),
        'grades_contemporary_world_with_peace_education': float(data.get('grades_contemporary_world_with_peace_education', 0.0)),
        'grades_mathematics_in_the_modern_world': float(data.get('grades_mathematics_in_the_modern_world', 0.0)),
        'grades_introduction_computing': float(data.get('grades_introduction_computing', 0.0)),
        'grades_fundamentals_of_programming': float(data.get('grades_fundamentals_of_programming', 0.0)),
        'study_hours': data.get('study_hours', '0.0'),
        'study_strategies': data.get('study_strategies', 'Unknown'),
        'regular_study_schedule': data.get('regular_study_schedule', 'Unknown'),
        'attendance_rate': data.get('attendance_rate', '0.0'),
        'class_participation': data.get('class_participation', '0.0'),
        'time_management_rating': data.get('time_management_rating', '0.0'),
        'study_deadlines_frequency': data.get('study_deadlines_frequency', '0.0'),
        'motivation_level': data.get('motivation_level', '0.0'),
        'engagement_level': data.get('engagement_level', '0.0'),
        'stress_frequency': data.get('stress_frequency', '0.0'),
        'coping_effectiveness': data.get('coping_effectiveness', '0.0')
    }

    # Convert to DataFrame
    input_df = pd.DataFrame([input_features])

    # Debugging: Print input features
    print("Input Features:", input_features)

    # Apply the same preprocessing used during model training
    processed_input = model.named_steps['preprocessor'].transform(input_df)

    # Debugging: Print processed input
    print("Processed Input:", processed_input)

    # Perform prediction
    prediction = model.named_steps['classifier'].predict(processed_input)[0]
    probability = model.named_steps['classifier'].predict_proba(processed_input)[:, 1][0] * 100
    output = "GRADUATE ON TIME" if prediction == 1 else "WILL NOT GRADUATE ON TIME"
    result = f"You have a {probability:.2f}% chance of graduating on time."

    # Get the average percentage for the specific student
    student_id = int(data.get('stud'))
    average_percentage = get_average_percentage(student_id)

    # Print the average percentage for debugging
    print(f"Average Percentage for Student ID {student_id}: {average_percentage:.2f}")

    # Generate comment and factor ID based on input
    comment, factor_id = generate_comment(input_features, prediction, average_percentage)
    remarks = output  # Use the prediction output as remarks

    # Set the intervention tag based on the remarks
    if remarks == "WILL NOT GRADUATE ON TIME":
        intervention_tag = "No"
    else:
        intervention_tag = None  # or "-" if you prefer dash

    # Save or update the prediction in the database
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()

            # Check if the prediction already exists for the student
            select_query = "SELECT Prediction FROM prediction WHERE StudentID = %s"
            cursor.execute(select_query, (student_id,))
            existing_record = cursor.fetchone()

            if existing_record:
                # If a prediction exists, update it
                existing_prediction = existing_record[0]
                if existing_prediction != probability:
                    update_query = """
                    UPDATE prediction
                    SET Prediction = %s, Remarks = %s, FactorID = %s, interventionTag = %s
                    WHERE StudentID = %s
                    """
                    cursor.execute(update_query, (probability, remarks, factor_id, intervention_tag, student_id))
                    connection.commit()
            else:
                # Insert a new record
                insert_query = """
                INSERT INTO prediction (StudentID, Prediction, Remarks, FactorID, interventionTag)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (student_id, probability, remarks, factor_id, intervention_tag))
                connection.commit()

            # Check if there are alerts for this student and delete them
            delete_query = "DELETE FROM alert WHERE StudentID = %s"
            cursor.execute(delete_query, (student_id,))
            connection.commit()  # Commit the delete operation

            cursor.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            connection.close()

    return jsonify({'result': result, 'output': output, 'comment': comment})


@views.route('/students')
def students():
    if "user_id" in session:
        user_id = session["user_id"]
        
        student_info = get_student_info(user_id)
        
        if student_info:
            student_id = student_info['StudentID']
            
            # Fetch student grades
            student_grades = get_student_grades(student_id)
            grades_archive = get_student_grades_archive(student_id)  # Fetch archived grades
            
            # Fetch prediction information
            prediction_info = fetch_prediction(student_id)  # Assuming this function is defined as shown before
            
            # Categorize current grades
            categorized_grades = {}
            for grade in student_grades:
                semester_name = grade['SemesterName']
                if semester_name not in categorized_grades:
                    categorized_grades[semester_name] = []
                if grade['SubjectID'] not in {g['SubjectID'] for g in categorized_grades[semester_name]}:
                    categorized_grades[semester_name].append(grade)

            # Categorize archived grades by year level and semester
            categorized_archive_grades = {}
            for grade in grades_archive:
                year_level = grade['YearLevelName']
                semester = grade['SemesterName']
                if year_level not in categorized_archive_grades:
                    categorized_archive_grades[year_level] = {}
                if semester not in categorized_archive_grades[year_level]:
                    categorized_archive_grades[year_level][semester] = []
                categorized_archive_grades[year_level][semester].append(grade)

            return render_template(
                "students.html",
                student_info=student_info,
                student_grades=categorized_grades,
                archive_grades=categorized_archive_grades,
                prediction_info=prediction_info  # Pass the prediction information to the template
            )
        else:
            flash("Student information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


#<!-- =============== ADMIN DASHBOARD ================ -->
@views.route('/admin')
def admin():
    if "user_id" in session:
        user_id = session["user_id"]
        admin_info = get_admin_info(user_id)
        if admin_info:
            student_count = get_student_count()
            professor_count = get_professor_count()
            admin_count = get_admin_count()
            subject_count = get_subject_count()
            return render_template("admin.html", 
                                   admin_info=admin_info,
                                   student_count=student_count,
                                   professor_count=professor_count,
                                   admin_count=admin_count,
                                   subject_count=subject_count)
        else:
            flash("Administrator information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


#<!-- =============== ADMIN USER ================ -->
@views.route('/adminUser', methods=['GET', 'POST'])
def adminUser():
    if "user_id" in session:
        if request.method == 'POST':
            # Extract form data
            role_id = request.form['role_id']
            username = request.form['username']
            password = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            class_id = request.form.get('class_id')  # Optional for students
            year_level_id = request.form.get('year_level_id')  # Optional for students
            specialization_id = request.form.get('specialization_id')  # Optional for students
            program_id = request.form.get('program_id')  # Optional for professors and students
            student_id = request.form.get('student_id')  # Student ID
            age = request.form.get('age')
            gender = request.form.get('gender')
            mother_occupation = request.form.get('mother_occupation')
            mother_salary = request.form.get('mother_salary')
            father_occupation = request.form.get('father_occupation')
            father_salary = request.form.get('father_salary')
            number_of_siblings = request.form.get('number_of_siblings')
            senior_high_school_average = request.form.get('senior_high_school_average')

            # Insert user using db module
            success = insert_user(role_id, username, password, first_name, last_name, email,
                                  program_id=program_id, class_id=class_id, year_level_id=year_level_id,
                                  specialization_id=specialization_id, student_id=student_id, age=age, gender=gender,
                                  mother_occupation=mother_occupation, mother_salary=mother_salary,
                                  father_occupation=father_occupation, father_salary=father_salary,
                                  number_of_siblings=number_of_siblings, senior_high_school_average=senior_high_school_average)

            # Flash message for successful user addition
            if success:
                flash("User added successfully!")
            else:
                flash(f"Failed to add user. Username '{username}' is already in use.", "error")

            # Redirect to the same page to refresh data
            return redirect(url_for('views.adminUser'))
        
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT admins.AdminID, users.UserID, admins.FirstName, admins.LastName, users.Username, admins.Email FROM admins INNER JOIN users ON admins.UserID = users.UserID"
                cursor.execute(query)
                admins = cursor.fetchall()

                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT professors.ProfessorID, users.Username, users.UserID, professors.FirstName, professors.LastName, professors.Email, collegeprograms.ProgramName
                    FROM professors
                    JOIN users ON professors.UserID = users.UserID
                    JOIN collegeprograms ON professors.ProgramID = collegeprograms.ProgramID
                """
                cursor.execute(query)
                professors = cursor.fetchall()
                
                cursor = connection.cursor(dictionary=True)
                query = """
                    SELECT students.StudentID, users.Username, users.UserID, students.FirstName, students.LastName, students.Email,
                        classes.ClassName, collegeprograms.ProgramName, specializations.SpecializationName,
                        yearlevels.YearLevelName
                    FROM students
                    JOIN users ON students.UserID = users.UserID
                    JOIN classes ON students.ClassID = classes.ClassID
                    JOIN collegeprograms ON students.ProgramID = collegeprograms.ProgramID
                    JOIN specializations ON students.SpecializationID = specializations.SpecializationID
                    JOIN yearlevels ON students.YearLevelID = yearlevels.YearLevelID
                """
                cursor.execute(query)
                students = cursor.fetchall()

                # Fetch data for dropdowns
                programs = get_program_list()  # Fetch program list
                specializations = get_specialization_list()  # Fetch specialization list
                classes = get_class_list()  # Fetch class list
                year_levels = get_year_level_list()  # Fetch year level list

                return render_template("adminUser.html", admins=admins, professors=professors, students=students,
                               programs=programs, specializations=specializations, classes=classes, year_levels=year_levels)
            except mysql.connector.Error as err:
                print(f"Error fetching admins: {err}")
            finally:
                cursor.close()
                connection.close()
        # Handle errors or return empty if no admins found
        return render_template("adminUser.html", admins=[], professors=[], students=[],
                               programs=programs, specializations=specializations, classes=classes, year_levels=year_levels) 
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

#<!-- =============== ADMIN MAINTENANCE ================ -->
@views.route('/adminMaintenance', methods=['GET', 'POST'])
def adminMaintenance():
    if "user_id" in session:
        if request.method == 'POST':
            form_type = request.form.get('form_type')

            if form_type == 'school_year':
                schoolyearid = request.form['schoolyearid']
                year = request.form['year']
                add_schoolyear(schoolyearid, year)
                flash('School year added successfully!')

            elif form_type == 'program':
                program_id = request.form['program_id']
                program_name = request.form['program_name']
                add_program(program_id, program_name)
                flash('Program added successfully!')

            elif form_type == 'specialization':
                specialization_id = request.form['specialization_id']
                specialization_name = request.form['specialization_name']
                program_name = request.form['program_name']
                add_specialization(specialization_id, specialization_name, program_name)
                flash('Specialization added successfully!')

            elif form_type == 'subject':
                subject_id = request.form['subject_id']  # This should be treated as a string
                print(f"SubjectID type: {type(subject_id)}, value: {subject_id}")
                subject_name = request.form['subject_name']
                subject_units = request.form['subject_units']
                subject_program_name = request.form['subject_program_name']
                add_subject(subject_id, subject_name, subject_units, subject_program_name)
                flash('Subject added successfully!')

            elif form_type == 'class':
                class_id = request.form['class_id']
                class_name = request.form['class_name']
                class_year = request.form['class_year']
                add_class(class_id, class_name, class_year)
                flash('Class added successfully!')

            elif form_type == 'professor_advisory':
                advisory_id = request.form['advisory_id']
                professor_id = request.form['professor_id']   # Corrected to match HTML form field name
                class_id = request.form['class_id']           # Corrected to match HTML form field name
                subject_id = request.form['subject_id']       # Corrected to match HTML form field name
                semester_id = request.form['semester_id']     # Corrected to match HTML form field name
                
                # Check for duplicates in the professor advisory
                success = add_professoradvisory(advisory_id, professor_id, class_id, subject_id, semester_id)
                if success:
                    flash('Professor Advisory added successfully!')
                else:
                    flash('A duplicate professor advisory was found. No new entry added.', 'error')

            return redirect(url_for('views.adminMaintenance'))

        # Fetch lists for displaying options in the form
        schoolyear = get_schoolyear_list()
        program = get_program_list()
        specialization = get_specialization_list()
        subject = get_subject_list()
        classes = get_classes_list()
        professoradvisory = get_professoradvisory_list()
        professors = get_professor_list()
        semesters = get_semesters_list()

        return render_template("adminMaintenance.html", 
                               schoolyear=schoolyear, 
                               program=program, 
                               specialization=specialization, 
                               subject=subject, 
                               classes=classes, 
                               professoradvisory=professoradvisory,
                               professors=professors,
                               semesters=semesters)
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    
#<!-- =============== ERROR UPDATE ================ -->
@views.route('/loadUpdatePage', methods=['GET'])
def loadUpdatePage():
    if "user_id" in session:
        form_type = request.args.get('form_type')
        id = request.args.get('id')
        data = None
        # Fetch necessary data for dropdowns if needed
        programs = get_program_list()
        schoolyears = get_schoolyear_list()
        professors = get_professoradvisory_list()
        classes = get_classes_list()
        subjects = get_subject_list()
        semesters = get_semesters_list()

        if form_type == 'school_year':
            data = get_schoolyear_by_id(id)
        elif form_type == 'program':
            data = get_program_by_id(id)
        elif form_type == 'specialization':
            data = get_specialization_by_id(id)
        elif form_type == 'subject':
            data = get_subject_by_id(id)
        elif form_type == 'class':
            data = get_class_by_id(id)
        elif form_type == 'professor_advisory':
            data = get_professoradvisory_by_id(id)
        
        return render_template("updateData.html", 
                               form_type=form_type, 
                               data=data,
                               programs=programs,
                               schoolyears=schoolyears,
                               professors=professors,
                               classes=classes,
                               subjects=subjects,
                               semesters=semesters)
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))

#<!-- =============== UPDATE FUNCTION FOR SCHOOL YEAR ================ -->
@views.route('/update_school_year/<int:id>', methods=['GET', 'POST'])
def update_school_year(id):
    if "user_id" in session:
        if request.method == 'GET':
            school_year = get_schoolyear_by_id(id)
            if school_year:
                return render_template('update_school_year.html', data=school_year)
            else:
                flash('School year not found!', 'error')
                return redirect(url_for('views.adminMaintenance'))
        
        elif request.method == 'POST':
            year = request.form['year']
            try:
                update_schoolyear(id, year)
                flash('School year updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating school year: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    
@views.route('/update_program/<int:id>', methods=['GET', 'POST'])
def update_program(id):
    if "user_id" in session:
        if request.method == 'GET':
            program_name = get_program_by_id(id)
            if program_name:
                return render_template('update_program.html', data=program_name)
            else:
                flash('Program not found!', 'error')
                return redirect(url_for('views.adminMaintenance'))
        
        elif request.method == 'POST':
            programName = request.form['programName']
            try:
                update_program_db(id, programName)  # Call the renamed function
                flash('Program Name updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating school year: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    
@views.route('/update_specialization/<int:id>', methods=['GET', 'POST'])
def update_specialization(id):
    if "user_id" in session:
        if request.method == 'GET':
            specialization_data = get_specialization_by_id(id)
            programs = get_program_list()  # Fetch the list of programs
            if specialization_data and programs:
                return render_template('update_specialization.html', data=specialization_data, programs=programs)
            else:
                flash('Specialization or programs not found!', 'error')
                return redirect(url_for('views.adminMaintenance'))
        
        elif request.method == 'POST':
            specialization_name = request.form['specialization_name']
            program_id = request.form['program_id']  # Get program ID from the form
            try:
                update_specialization_db(id, specialization_name, program_id)
                flash('Specialization updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating specialization: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))

@views.route('/update_subject/<subject_id>', methods=['GET', 'POST'])
def update_subject(subject_id):
    if "user_id" in session:
        if request.method == 'GET':
            subject_data = get_subject_by_id(subject_id)
            programs = get_program_list()
            if subject_data and programs:
                return render_template('update_subject.html', data=subject_data, programs=programs)
            else:
                flash('Subject or programs not found!', 'error')
                return redirect(url_for('views.adminMaintenance'))
        
        elif request.method == 'POST':
            subject_name = request.form['subject_name']
            subject_units = request.form['subject_units']
            program_id = request.form['program_id']
            try:
                update_subject_db(subject_id, subject_name, subject_units, program_id)
                flash('Subject updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating subject: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


@views.route('/update_class/<int:id>', methods=['GET', 'POST'])
def update_class(id):
    if "user_id" in session:
        class_data = get_class_by_id(id)
        classes = get_class_list()
        school_years = get_schoolyear_list()

        if not class_data:
            flash('Class not found!', 'error')
            return redirect(url_for('views.adminMaintenance'))

        if request.method == 'GET':
            return render_template('update_class.html', data=class_data, classes=classes, school_years=school_years)

        elif request.method == 'POST':
            try:
                class_name = request.form['class_name']
                year = request.form['year']

                print(f"Received form data - class_name: {class_name}, year: {year}")

                update_class_db(id, class_name, year)
                flash('Class updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except KeyError as e:
                flash(f'Missing form field: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating class: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


@views.route('/update_professoradvisory/<int:id>', methods=['GET', 'POST'])
def update_professoradvisory(id):
    if "user_id" in session:
        advisory_data = get_professoradvisory_by_id(id)

        if not advisory_data:
            flash('Professor advisory not found!', 'error')
            return redirect(url_for('views.adminMaintenance'))

        if request.method == 'GET':
            # Fetch additional data needed for the form (e.g., list of professors, classes, subjects, semesters)
            professors = get_professor_list()
            classes = get_class_list()
            subjects = get_subject_list()
            semesters = get_semesters_list()

            return render_template('update_professoradvisory.html', data=advisory_data, professors=professors, classes=classes, subjects=subjects, semesters=semesters)

        elif request.method == 'POST':
            try:
                professor_id = request.form['professor_id']
                class_id = request.form['class_id']
                subject_id = request.form['subject_id']
                semester_id = request.form['semester_id']

                update_professoradvisory_db(id, professor_id, class_id, subject_id, semester_id)
                flash('Professor advisory updated successfully!')
                return redirect(url_for('views.adminMaintenance'))
            except KeyError as e:
                flash(f'Missing form field: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
            except Exception as e:
                flash(f'Error updating professor advisory: {str(e)}', 'error')
                return redirect(url_for('views.adminMaintenance'))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))







#<!-- =============== ERROR UPDATE ================ -->
@views.route('/updateData', methods=['POST'])
def updateData():
    if "user_id" in session:
        form_type = request.form.get('form_type')
        id = request.form.get('id')
        
        try:
            if form_type == 'school_year':
                schoolyear_id = request.form['schoolyear_id']
                year = request.form['year']
                update_schoolyear(schoolyear_id, year)
                flash('School year updated successfully!')
            
            elif form_type == 'program':
                program_id = request.form['program_id']
                program_name = request.form['program_name']
                update_program(program_id, program_name)
                flash('Program updated successfully!')
            
            elif form_type == 'specialization':
                specialization_id = request.form['specialization_id']
                specialization_name = request.form['specialization_name']
                program_id = request.form['program_id']
                update_specialization(specialization_id, specialization_name, program_id)
                flash('Specialization updated successfully!')
            
            elif form_type == 'subject':
                subject_id = request.form['subject_id']
                subject_name = request.form['subject_name']
                subject_units = request.form['subject_units']
                program_id = request.form['program_id']
                update_subject(subject_id, subject_name, subject_units, program_id)
                flash('Subject updated successfully!')
            
            elif form_type == 'class':
                class_id = request.form['class_id']
                class_name = request.form['class_name']
                schoolyear_id = request.form['schoolyear_id']
                update_class(class_id, class_name, schoolyear_id)
                flash('Class updated successfully!')
            
            elif form_type == 'professor_advisory':
                advisory_id = request.form['advisory_id']
                professor_id = request.form['professor_id']
                class_id = request.form['class_id']
                subject_id = request.form['subject_id']
                semester_id = request.form['semester_id']
                update_professoradvisory(advisory_id, professor_id, class_id, subject_id, semester_id)
                flash('Professor Advisory updated successfully!')
            
            return redirect(url_for('views.adminMaintenance'))
        
        except Exception as e:
            error_msg = f'Error updating: {str(e)}'
            logging.error(error_msg)  # Log the error for debugging
            flash(error_msg, 'error')  # Flash the error message
            return redirect(url_for('views.adminMaintenance'))
    
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

#<!-- =============== ADMIN UPLOAD DASHBOARD ================ -->
@views.route('/adminUpload')
def adminUpload():
    if "user_id" in session:
        user_id = session["user_id"]
        admin_info = get_admin_info(user_id)
        if admin_info:
            student_count = get_student_count()
            professor_count = get_professor_count()
            admin_count = get_admin_count()
            subject_count = get_subject_count()
            return render_template("adminUpload.html", 
                                   admin_info=admin_info,
                                   student_count=student_count,
                                   professor_count=professor_count,
                                   admin_count=admin_count,
                                   subject_count=subject_count)
        else:
            flash("Administrator information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


#<!-- =============== PROFESSOR DASHBOARD ================ -->
@views.route('/professors')
def professors():
    if "user_id" in session:
        user_id = session["user_id"]
        professors_info = get_professors_info(user_id)
        if professors_info:
            professor_id = professors_info['ProfessorID']
            classes_subjects = get_professor_classes_subjects(professor_id)
            
            # Render the template with the appropriate message if no classes are found
            return render_template(
                "professors.html",
                professors_info=professors_info,
                classes_subjects=classes_subjects,
                no_classes_message=not classes_subjects
            )
        else:
            flash("Professor information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


@views.route('/class/<int:class_id>/subject/<string:subject_id>/students')
def class_students(class_id, subject_id):
    enrolled_students = get_students_by_class(class_id, subject_id)
    if enrolled_students:
        class_details = {
            "ClassName": enrolled_students[0]['ClassName'],
            "SubjectName": enrolled_students[0]['SubjectName'],
            "SemesterName": enrolled_students[0]['SemesterName']
        }
        school_year_id = enrolled_students[0]['SchoolYearID']
        semester_id = enrolled_students[0]['SemesterID']

        user_id = session.get('user_id')
        professor_id = get_professor_id_by_user_id(user_id)
        
        # Calculate average grades for students
        for student in enrolled_students:
            midterm_grade = student['MidtermGrade']
            final_grade = student['FinalGrade']
            if midterm_grade and final_grade:
                student['AverageGrade'] = (midterm_grade + final_grade) / 2
            elif midterm_grade:
                student['AverageGrade'] = midterm_grade
            elif final_grade:
                student['AverageGrade'] = final_grade
            else:
                student['AverageGrade'] = None
        
        return render_template('class_students.html', enrolled_students=enrolled_students, class_details=class_details, class_id=class_id, subject_id=subject_id, school_year_id=school_year_id, semester_id=semester_id, professor_id=professor_id)
    else:
        flash("No students found for this class.")
        return redirect(url_for('views.professors'))







@views.route('/submit_grades', methods=['POST'])
def submit_grades():
    if request.method == 'POST':
        students_grades = []
        
        professor_id = request.form.get('professor_id')

        for key, value in request.form.items():
            if key.startswith('student_id_'):
                student_id = key.split('_')[2]
                subject_id = request.form.get('subject_id')
                midterm_grade = request.form.get(f'midterm_grade_{student_id}')
                final_grade = request.form.get(f'final_grade_{student_id}')
                # Compute average grade
                if midterm_grade and final_grade:
                    average_grade = (float(midterm_grade) + float(final_grade)) / 2
                elif midterm_grade:
                    average_grade = float(midterm_grade)
                elif final_grade:
                    average_grade = float(final_grade)
                else:
                    average_grade = None
                class_id = request.form.get('class_id')
                school_year_id = request.form.get('school_year_id')
                semester_id = request.form.get('semester_id')
                
                if professor_id is None:
                    flash('Professor ID not found in form data.')
                    return redirect(url_for('views.professors'))

                students_grades.append((student_id, subject_id, professor_id, midterm_grade, final_grade, average_grade, school_year_id, semester_id, class_id))
    
        save_grades(students_grades)
        return redirect(url_for('views.professors'))
    else:
        flash('Method not allowed')
        return redirect(url_for('views.professors'))



def save_grades(students_grades):
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor()
        for grade in students_grades:
            student_id, subject_id, professor_id, midterm_grade, final_grade, average_grade, school_year_id, semester_id, class_id = grade
            
            query = """
                SELECT GradeID FROM grades
                WHERE StudentID = %s AND SubjectID = %s AND ClassID = %s
            """
            cursor.execute(query, (student_id, subject_id, class_id))
            existing_grade = cursor.fetchone()
            
            if existing_grade:
                query = """
                    UPDATE grades
                    SET MidtermGrade = %s, FinalGrade = %s, AverageGrade = %s
                    WHERE GradeID = %s
                """
                cursor.execute(query, (midterm_grade, final_grade, average_grade, existing_grade[0]))
            else:
                query = """
                    INSERT INTO grades (StudentID, SubjectID, ProfessorID, MidtermGrade, FinalGrade, AverageGrade, SchoolYearID, SemesterID, ClassID)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, grade)
                
        connection.commit()
        connection.close()
        flash('Grades submitted successfully!')














#<!-- =============== STUDENT DASHBOARD ================ -->
@views.route('/student-dashboard')
def studentDashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        student_info = get_student_info(user_id)
        if student_info:
            return render_template("student_dashboard.html", student_info=student_info)
        else:
            flash("Student information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

#----------------------------------------------------------------------------------------------------

#<!-- =============== USER TEMPLATE ================ -->
@views.route('/user')
def user():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT admins.AdminID, users.UserID, admins.FirstName, admins.LastName, users.Username, admins.Email FROM admins INNER JOIN users ON admins.UserID = users.UserID"
            cursor.execute(query)
            admins = cursor.fetchall()
            return render_template("user.html", admins=admins)
        except mysql.connector.Error as err:
            print(f"Error fetching admins: {err}")
        finally:
            cursor.close()
            connection.close()
    # Handle errors or return empty if no admins found
    return render_template("user.html", admins=[])


#<!-- =============== FUNCTION FOR UPDATING ADMIN USER ================ -->
@views.route('/update/<int:admin_id>', methods=['GET', 'POST'])
def update_admin(admin_id):
    connection = connect_to_database()
    cursor = None
    if connection:
        if request.method == 'GET':
            try:
                cursor = connection.cursor(dictionary=True)
                query = """SELECT admins.AdminID, users.UserID, users.Password, admins.FirstName, 
                           admins.LastName, users.Username, admins.Email 
                           FROM admins 
                           INNER JOIN users ON admins.UserID = users.UserID 
                           WHERE admins.AdminID = %s"""
                cursor.execute(query, (admin_id,))
                admin = cursor.fetchone()
                if admin:
                    return render_template("update_admin.html", admin=admin)
                else:
                    flash(f"Admin with ID {admin_id} not found", "error")
                    return redirect(url_for('views.adminUser'))
            except mysql.connector.Error as err:
                print(f"Error fetching admin: {err}")
                flash("Error fetching admin", "error")
            finally:
                if cursor:
                    cursor.close()
                connection.close()

        elif request.method == 'POST':
            try:
                cursor = connection.cursor(dictionary=True)
                username = request.form.get('username')
                password = request.form.get('password')  # Optional password input
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                email = request.form.get('email')

                query = "SELECT UserID FROM admins WHERE AdminID = %s"
                cursor.execute(query, (admin_id,))
                admin = cursor.fetchone()

                if admin:
                    # Update the user details
                    if password:  # If a new password is provided, hash and update it
                        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        query = "UPDATE users SET Username = %s, Password = %s WHERE UserID = %s"
                        cursor.execute(query, (username, hashed_password, admin['UserID']))
                    else:
                        # If no password is provided, update only the username
                        query = "UPDATE users SET Username = %s WHERE UserID = %s"
                        cursor.execute(query, (username, admin['UserID']))
                    
                    connection.commit()

                    # Update the admin details
                    query = "UPDATE admins SET FirstName = %s, LastName = %s, Email = %s WHERE AdminID = %s"
                    cursor.execute(query, (first_name, last_name, email, admin_id))
                    connection.commit()

                    flash("Admin details updated successfully", "success")
                    return redirect(url_for('views.adminUser'))
                else:
                    flash("Admin not found", "error")
            except mysql.connector.Error as err:
                print(f"Error updating admin: {err}")
                flash("Error updating admin", "error")
            finally:
                if cursor:
                    cursor.close()
                connection.close()

    flash("Unable to update admin", "error")
    return redirect(url_for('views.user'))



@views.route('/update/credentials/<int:user_id>', methods=['GET', 'POST'])
def update_credentials(user_id):
    connection = connect_to_database()
    if connection:
        if request.method == 'GET':
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT UserID, Username, Password FROM users WHERE UserID = %s"
                cursor.execute(query, (user_id,))
                user = cursor.fetchone()
                if user:
                    return render_template("update_credentials.html", user=user)
                else:
                    flash(f"User with ID {user_id} not found", "error")
                    return redirect(url_for('views.user'))
            except mysql.connector.Error as err:
                print(f"Error fetching user: {err}")
                flash("Error fetching user", "error")
            finally:
                cursor.close()
                connection.close()
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                cursor = connection.cursor()
                query = "UPDATE users SET Username = %s, Password = %s WHERE UserID = %s"
                cursor.execute(query, (username, password, user_id))
                connection.commit()
                flash("Username and password updated successfully", "success")
            except mysql.connector.Error as err:
                print(f"Error updating username and password: {err}")
                flash("Error updating username and password", "error")
            finally:
                cursor.close()
                connection.close()
                return redirect(url_for('views.adminUser'))

    flash("Unable to update username and password", "error")
    return redirect(url_for('views.adminUser'))


#<!-- =============== FUNCTION FOR UPDATING PROFESSOR USER ================ -->
@views.route('/update_professor/<int:professor_id>', methods=['GET', 'POST'])
def update_professor(professor_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            if request.method == 'GET':
                query = ("SELECT professors.ProfessorID, users.UserID, professors.FirstName, professors.LastName, "
                         "users.Username, users.Password, professors.Email, professors.ProgramID "
                         "FROM professors INNER JOIN users ON professors.UserID = users.UserID WHERE professors.ProfessorID = %s")
                cursor.execute(query, (professor_id,))
                professor = cursor.fetchone()
                cursor.close()

                if professor:
                    programs = get_program_list()  # Fetch program list for dropdown
                    return render_template("update_professor.html", professor=professor, programs=programs)
                else:
                    flash(f"Professor with ID {professor_id} not found", "error")
                    return redirect(url_for('views.adminUser'))

            elif request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')  # Optional password input
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                email = request.form.get('email')
                program_id = request.form.get('program_id')

                # Fetch professor again to get UserID
                query = ("SELECT UserID FROM professors WHERE ProfessorID = %s")
                cursor.execute(query, (professor_id,))
                professor = cursor.fetchone()

                if professor:
                    if password:  # Only update password if a new one is provided
                        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        query = "UPDATE users SET Username = %s, Password = %s WHERE UserID = %s"
                        cursor.execute(query, (username, hashed_password, professor['UserID']))
                    else:
                        # Update other user details, leave password unchanged
                        query = "UPDATE users SET Username = %s WHERE UserID = %s"
                        cursor.execute(query, (username, professor['UserID']))

                    connection.commit()

                    # Update professor details
                    query = ("UPDATE professors SET FirstName = %s, LastName = %s, Email = %s, ProgramID = %s WHERE ProfessorID = %s")
                    cursor.execute(query, (first_name, last_name, email, program_id, professor_id))
                    connection.commit()
                    cursor.close()

                    flash("Professor details updated successfully", "success")
                    return redirect(url_for('views.adminUser'))

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            flash("Error updating professor, Username might already exist.", "error")

        finally:
            connection.close()

    flash("Unable to update professor", "error")
    return redirect(url_for('views.adminUser'))


#<!-- =============== FUNCTION FOR UPDATING STUDENT USER ================ -->
@views.route('/update_student/<int:student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        if request.method == 'GET':
            query = ("SELECT students.StudentID, users.Username, students.FirstName, students.LastName, students.Email, "
                     "students.ProgramID, students.ClassID, students.SpecializationID, students.YearLevelID, "
                     "students.Age, students.Gender, students.MotherOccupation, students.MotherSalary, "
                     "students.FatherOccupation, students.FatherSalary, students.NumberOfSiblings, students.SeniorHighSchoolAverage "
                     "FROM students "
                     "INNER JOIN users ON students.UserID = users.UserID "
                     "WHERE students.StudentID = %s")
            cursor.execute(query, (student_id,))
            student = cursor.fetchone()

            if not student:
                flash(f"Student with ID {student_id} not found", "error")
                return redirect(url_for('views.adminUser'))

            programs = get_program_list()
            specializations = get_specialization_list()
            classes = get_class_list()
            year_levels = get_year_level_list()

            return render_template("update_student.html", student=student, programs=programs, specializations=specializations, classes=classes, year_levels=year_levels)

        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')  # Optional password input
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            program_id = request.form.get('program_id')
            class_id = request.form.get('class_id')
            specialization_id = request.form.get('specialization_id')
            year_level_id = request.form.get('year_level_id')
            age = request.form.get('age')
            gender = request.form.get('gender')
            mother_occupation = request.form.get('mother_occupation')
            mother_salary = request.form.get('mother_salary')
            father_occupation = request.form.get('father_occupation')
            father_salary = request.form.get('father_salary')
            number_of_siblings = request.form.get('number_of_siblings')
            senior_high_school_average = request.form.get('senior_high_school_average')

            query = "SELECT UserID FROM students WHERE StudentID = %s"
            cursor.execute(query, (student_id,))
            student = cursor.fetchone()

            if student:
                # If a new password is provided, hash and update it
                if password:
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    query = "UPDATE users SET Username = %s, Password = %s WHERE UserID = %s"
                    cursor.execute(query, (username, hashed_password, student['UserID']))
                else:
                    # If no password is provided, update only the username
                    query = "UPDATE users SET Username = %s WHERE UserID = %s"
                    cursor.execute(query, (username, student['UserID']))
                
                connection.commit()

                # Update student details
                query = ("UPDATE students SET FirstName = %s, LastName = %s, Email = %s, ProgramID = %s, "
                         "ClassID = %s, SpecializationID = %s, YearLevelID = %s, Age = %s, Gender = %s, "
                         "MotherOccupation = %s, MotherSalary = %s, FatherOccupation = %s, FatherSalary = %s, "
                         "NumberOfSiblings = %s, SeniorHighSchoolAverage = %s WHERE StudentID = %s")
                cursor.execute(query, (first_name, last_name, email, program_id, class_id, specialization_id, year_level_id,
                                       age, gender, mother_occupation, mother_salary, father_occupation, father_salary,
                                       number_of_siblings, senior_high_school_average, student_id))
                connection.commit()

                flash(f"Student {first_name} {last_name} has been updated successfully!", "success")
                return redirect(url_for('views.adminUser'))

    except mysql.connector.Error as err:
        flash(f"Error: {err}", "error")

    finally:
        if cursor:
            cursor.close()
        connection.close()

    return redirect(url_for('views.adminUser'))

@views.route('/get_graduation_data')
def get_graduation_data():
    try:
        connection = connect_to_database()
        cursor = connection.cursor()
        query = """
            SELECT 
                CASE 
                    WHEN Prediction >= 50.0 THEN 'Will Graduate On Time'
                    ELSE 'Will Not Graduate On Time'
                END AS category,
                COUNT(*) as count
            FROM prediction
            GROUP BY category
        """
        cursor.execute(query)
        results = cursor.fetchall()
        total_students = sum(row[1] for row in results)
        labels = [row[0] for row in results]
        values = [(row[1] / total_students) * 100 for row in results]
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@views.route('/delete/admin/<int:admin_id>', methods=['GET'])
def delete_admin(admin_id):
    try:
        # Connect to the database
        connection = connect_to_database()  # Assuming this function is defined
        cursor = connection.cursor(dictionary=True)  # Use dictionary cursor

        # Retrieve the admin details before deletion
        cursor.execute("SELECT * FROM admins WHERE AdminID = %s", (admin_id,))
        admin_data = cursor.fetchone()

        if not admin_data:
            flash('Admin not found', 'error')
            return redirect(url_for('views.adminUser'))

        # Move the admin data to the admins_archive table
        cursor.execute("""
            INSERT INTO admins_archive (AdminID, UserID, FirstName, LastName, Email)
            VALUES (%s, %s, %s, %s, %s)
        """, (admin_data['AdminID'], admin_data['UserID'], admin_data['FirstName'], admin_data['LastName'], admin_data['Email']))

        # Delete the admin from the admins table
        cursor.execute("DELETE FROM admins WHERE AdminID = %s", (admin_id,))

        # Commit the changes
        connection.commit()

        flash('Admin Archived Successfully', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'error')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('views.adminUser'))

@views.route('/delete_professor/<int:professor_id>', methods=['GET'])
def delete_professor(professor_id):
    try:
        # Connect to the database
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        # Retrieve the professor's details before deletion
        cursor.execute("SELECT * FROM professors WHERE ProfessorID = %s", (professor_id,))
        professor_data = cursor.fetchone()

        if not professor_data:
            flash('Professor not found', 'error')
            return redirect(url_for('views.adminUser'))  # Replace with your actual route for the professor list

        # Move the professor data to the professors_archive table
        cursor.execute("""
            INSERT INTO professors_archive (ProfessorID, UserID, FirstName, LastName, Email, ProgramID)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (professor_data['ProfessorID'], professor_data['UserID'], professor_data['FirstName'],
              professor_data['LastName'], professor_data['Email'], professor_data['ProgramID']))

        # Delete the professor from the professors table
        cursor.execute("DELETE FROM professors WHERE ProfessorID = %s", (professor_id,))

        # Commit the changes
        connection.commit()

        flash('Professor Archived Successfully', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'error')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('views.adminUser'))  # Replace with the actual route for the professor list

# Assuming this is inside the 'views' Blueprint
@views.route('/delete_student/<int:student_id>', methods=['POST', 'GET'])
def delete_student(student_id):
    # Fetch the student from the `students` table
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE StudentID = %s", (student_id,))
    student = cursor.fetchone()

    if student:
        try:
            # Move the student to `students_archive` table
            cursor.execute("""
                INSERT INTO students_archive (StudentID, UserID, FirstName, LastName, ClassID, ProgramID, Email, SpecializationID, YearLevelID, Age, Gender,
                                              MotherOccupation, MotherSalary, FatherOccupation, FatherSalary, NumberOfSiblings, SeniorHighSchoolAverage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (student['StudentID'], student['UserID'], student['FirstName'], student['LastName'], student['ClassID'], student['ProgramID'], 
                  student['Email'], student['SpecializationID'], student['YearLevelID'], student['Age'], student['Gender'], 
                  student['MotherOccupation'], student['MotherSalary'], student['FatherOccupation'], student['FatherSalary'], 
                  student['NumberOfSiblings'], student['SeniorHighSchoolAverage']))

            # Delete the student from the `students` table
            cursor.execute("DELETE FROM students WHERE StudentID = %s", (student_id,))
            connection.commit()  # Commit the transaction

            flash('Student Archived Successfully', 'success')
        except Exception as e:
            connection.rollback()  # Rollback the transaction in case of error
            flash('Error occurred while deleting the student: {}'.format(e), 'error')
    else:
        flash('Student not found.', 'error')

    return redirect(url_for('views.adminUser'))  

@views.route('/students_behavioral', methods=['GET', 'POST'])
def handle_behavioral_survey():
    if "user_id" in session:
        user_id = session["user_id"]
        
        # Fetch student information
        student_info = get_student_info(user_id)
        
        if student_info:
            student_id = student_info['StudentID']
        else:
            flash('Student information not found.')
            return redirect(url_for('views.studentBehavioral'))
        
    else:
        flash('User is not logged in.')
        return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        # Retrieve form data
        study_hours = request.form.get('study_hours')
        study_strategies = request.form.get('study_strategies')
        study_schedule = request.form.get('study_schedule')
        attendance_rate = request.form.get('attendance_rate')
        participation = request.form.get('participation')
        time_management = request.form.get('time_management')
        study_deadlines = request.form.get('study_deadlines')
        motivation = request.form.get('motivation')
        engagement = request.form.get('engagement')
        academic_stress = request.form.get('academic_stress')
        coping_mechanisms = request.form.get('coping_mechanisms')

        # Connect to the database
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                # Insert the data into the behavioral table, including StudentID
                query = '''
                INSERT INTO behavioral (StudentID, StudyHours, StudyStrategies, RegularStudySchedule, AttendanceRate, 
                                        ClassParticipation, TimeManagementRating, StudyDeadlinesFrequency, MotivationLevel, 
                                        EngagementLevel, StressFrequency, CopingEffectiveness)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''
                cursor.execute(query, (student_id, study_hours, study_strategies, study_schedule, attendance_rate, 
                                       participation, time_management, study_deadlines, motivation, engagement, 
                                       academic_stress, coping_mechanisms))
        
                # Commit the changes to the database
                connection.commit()

                flash('Survey data submitted successfully!')
                return redirect(url_for('views.studentBehavioral'))
            
            except Exception as e:
                flash(f'Error submitting data: {str(e)}')
                return redirect(url_for('views.studentBehavioral'))
            
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed.')
            return redirect(url_for('views.studentBehavioral'))
    
    return render_template('student_behavioral.html')

@views.route('/get-interventions')
def get_interventions():
    # Connect to the database
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Fetch all events
    cursor.execute('SELECT * FROM theevents')
    events = cursor.fetchall()

    # Close the connection
    cursor.close()
    connection.close()

    # Print fetched events for debugging
    print("Fetched events:", events)  # Debug print

    # For each event, add the correct image path and filter out EventID 0
    filtered_events = []
    for event in events:
        if event['EventID'] != 0:  # Filter out events with ID 0
            if event['Picture']:
                event['ImagePath'] = f"/static/upload/{event['Picture']}"
            else:
                event['ImagePath'] = "/static/images/default.jpg"
            filtered_events.append(event)  # Only add the non-zero ID events
    return jsonify(filtered_events)  # Return the filtered list of events


# Route for handling the form submission and inserting data into the interventions table
@views.route('/interventions/add', methods=['POST'])
def add_intervention():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        picture = request.files['picture']
        location = request.form['location']
        date = request.form['date']
        time = request.form['time']
        factor_id = request.form['factor_id']  # New dropdown for FactorID

        # Define dynamic path for the upload folder
        upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'upload')

        # Ensure the upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Save the picture file to the 'static/upload' folder
        picture_filename = picture.filename
        picture_path = os.path.join(upload_folder, picture_filename)
        picture.save(picture_path)
        
        try:
            # Connect to the database
            connection = connect_to_database()
            cursor = connection.cursor()

            # SQL query to insert data into theEvents table
            sql = """
            INSERT INTO theevents (Title, Description, Link, Picture, Location, Date, Time, FactorID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Execute the SQL query with form data
            cursor.execute(sql, (title, description, link, picture_filename, location, date, time, factor_id))

            # Commit the transaction
            connection.commit()
            flash('Event added successfully!', 'success')

        except Exception as e:
            connection.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('views.adminMaintenance'))
    
@views.route('/studentsEvent', methods=['GET', 'POST'])
def studentsEvent():
    if "user_id" not in session:
        flash('User is not logged in.')
        return redirect(url_for('auth.login'))

    user_id = session["user_id"]

    # Connect to the database
    connection = None
    try:
        # Assuming you're using MySQL, make sure the connection function is correctly implemented
        connection = connect_to_database()  # or replace with appropriate connection method
        cursor = connection.cursor(dictionary=True)

        # Fetch events for GET request to render the page
        cursor.execute("SELECT * FROM theevents")  # Change to fetch from 'theevents' table
        events = cursor.fetchall()

        # Render the page with events data
        return render_template("studentsEvent.html", events=events)

    except Exception as e:
        print(f"Error establishing database connection: {e}")
        return jsonify({'message': 'Database connection failed'}), 500

    finally:
        if connection:
            cursor.close()


@views.route('/delete_school_year/<int:id>', methods=['GET', 'POST'])
def delete_school_year(id):
    try:
        # Establish the connection
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        # Disable foreign key checks
        cursor.execute('SET FOREIGN_KEY_CHECKS = 0;')

        # Archive `grades` to `grades_archive`
        cursor.execute('''
            INSERT INTO grades_archive (GradeID, StudentID, SubjectID, ProfessorID, MidtermGrade, FinalGrade, SchoolYearID, SemesterID, ClassID, AverageGrade)
            SELECT GradeID, StudentID, SubjectID, ProfessorID, MidtermGrade, FinalGrade, SchoolYearID, SemesterID, ClassID, AverageGrade
            FROM grades
            WHERE SchoolYearID = %s
        ''', (id,))
        
        # Archive `professoradvisory` to `professoradvisory_archive`
        cursor.execute('''
            INSERT INTO professoradvisory_archive (AdvisoryID, ProfessorID, ClassID, SubjectID, SemesterID)
            SELECT AdvisoryID, ProfessorID, ClassID, SubjectID, SemesterID
            FROM professoradvisory
            WHERE ClassID IN (SELECT ClassID FROM classes WHERE SchoolYearID = %s)
        ''', (id,))
        
        # Archive `classes` to `classes_archive`
        cursor.execute('''
            INSERT INTO classes_archive (ClassID, ClassName, SchoolYearID)
            SELECT ClassID, ClassName, SchoolYearID
            FROM classes
            WHERE SchoolYearID = %s
        ''', (id,))
        
        # Archive `schoolyear` to `schoolyear_archive`
        cursor.execute('''
            INSERT INTO schoolyear_archive (SchoolYearID, Year)
            SELECT SchoolYearID, Year
            FROM schoolyear
            WHERE SchoolYearID = %s
        ''', (id,))
        
        # Delete the data from the original tables
        cursor.execute('DELETE FROM grades WHERE SchoolYearID = %s', (id,))
        cursor.execute('DELETE FROM professoradvisory WHERE ClassID IN (SELECT ClassID FROM classes WHERE SchoolYearID = %s)', (id,))
        cursor.execute('DELETE FROM classes WHERE SchoolYearID = %s', (id,))
        cursor.execute('DELETE FROM schoolyear WHERE SchoolYearID = %s', (id,))

        # Enable foreign key checks again
        cursor.execute('SET FOREIGN_KEY_CHECKS = 1;')
        
        # Commit the transaction
        connection.commit()
        
        flash('School year and related data have been archived and deleted successfully.', 'success')
        return redirect(url_for('views.adminMaintenance'))  # Redirect to the page showing school years

    except Exception as e:
        # Rollback in case of error
        connection.rollback()
        flash(f'Error deleting school year: {str(e)}', 'error')
        return redirect(url_for('views.adminMaintenance'))

    finally:
        # Close the cursor and connection
        cursor.close()
        connection.close()

@views.route('/delete-event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    connection = connect_to_database()
    cursor = connection.cursor()

    try:
        # Delete from the theevents table using EventID
        cursor.execute('DELETE FROM theevents WHERE EventID = %s', (event_id,))
        
        connection.commit()  # Commit the changes
        return jsonify({"success": True, "message": "Event deleted successfully."}), 200
    except Exception as e:
        connection.rollback()  # Roll back if there's an error
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Function to save the uploaded picture
def save_picture(picture):
    # Define the upload path using the absolute path setup
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'upload')
    
    # Create the directory if it doesn't exist
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Secure filename and save
    filename = secure_filename(picture.filename)
    picture_path = os.path.join(upload_folder, filename)
    picture.save(picture_path)
    
    # Return just the filename to store in the database
    return filename

@views.route('/update-event/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    # Connect to the database
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Handle GET request to fetch existing event data
    if request.method == 'GET':
        cursor.execute('SELECT * FROM theEvents WHERE EventID = %s', (event_id,))
        event = cursor.fetchone()  # Fetch the event data

        # Check if event was found
        if event is None:
            cursor.close()
            connection.close()
            return "Event not found", 404  # Return a 404 if no event is found

        cursor.close()
        connection.close()
        return render_template('update_events.html', event=event)  # Render the update form

    # Handle POST request to update event data
    elif request.method == 'POST':
        # Check if the event exists
        cursor.execute('SELECT * FROM theEvents WHERE EventID = %s', (event_id,))
        event = cursor.fetchone()  # Fetch again to ensure it's still valid

        if event is None:
            cursor.close()
            connection.close()
            return "Event not found", 404  # Handle the case where the event does not exist

        # Get form data
        title = request.form['title']
        description = request.form['description']
        link = request.form['link']
        location = request.form['location']
        date = request.form['date']
        time = request.form['time']
        factor_id = request.form['factor_id']  # Capture FactorID from form

        # Handle the picture upload
        picture_path = None
        if 'picture' in request.files:
            picture = request.files['picture']
            if picture and picture.filename != '':
                # Save the picture and get its path
                picture_path = save_picture(picture)  # Save the file and return the path

        # Update the database
        try:
            cursor.execute(''' 
                UPDATE theEvents 
                SET Title = %s, Description = %s, Link = %s, Location = %s, Date = %s, Time = %s, Picture = %s, FactorID = %s
                WHERE EventID = %s
            ''', (
                title,
                description,
                link,
                location,
                date,
                time,
                picture_path if picture_path else event['Picture'],  # Use existing picture if no new one uploaded
                factor_id,  # FactorID value from form
                event_id
            ))

            connection.commit()
            return redirect(url_for('views.adminMaintenance'))  # Redirect after updating
        except Exception as e:
            connection.rollback()  # Rollback if there's an error
            flash("Error updating the event: " + str(e))  # Use flash messages to inform the user
            return render_template('update_events.html', event=event)
        finally:
            cursor.close()
            connection.close()

    
@views.route('/adminArchive', methods=['GET', 'POST'])
def adminArchive():
    if "user_id" in session:
        if request.method == 'POST':
            schoolyear_id = request.form.get('schoolyear')
            print(f"SchoolYearID passed: {schoolyear_id}")  # Debug statement to check the school year ID
            if archive_schoolyear_data(schoolyear_id):
                flash("Data archived successfully!", "success")
            else:
                flash("Failed to archive data.", "error")
            return redirect(url_for('views.adminArchive'))
        
        # Fetch active and archived school years data
        schoolyears = get_schoolyear_list()  # Fetch current school year data
        archived_schoolyears = get_archived_schoolyears()  # Fetch archived school years
        
        # Pass both lists to the template
        return render_template("adminArchive.html", schoolyears=schoolyears, archived_schoolyears=archived_schoolyears)
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

@views.route('/adminPrediction')
def adminPrediction():
    if "user_id" in session:
        user_id = session["user_id"]
        student_predictions = get_student_predictions()

        # Render the template regardless of whether predictions are found
        return render_template("adminPrediction.html", student_predictions=student_predictions)
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

@views.route('/perform_academic_intervention', methods=['POST'])
def perform_academic_intervention():
    if "user_id" in session:
        # Call the intervention function based on the student's factor in prediction
        perform_intervention_based_on_factor()
        flash("Interventions logged successfully for students at risk.")
        return redirect(url_for("views.adminPrediction"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

@views.route('/professorAdditionalAcadReq')
def professorAdditionalAcadReq():
    if "user_id" in session:
        user_id = session["user_id"]
        
        # Fetch professor info based on user_id
        professors_info = get_professors_info(user_id)
        
        if professors_info:
            professor_id = professors_info['ProfessorID']  # Assuming you get this field
            
            # Fetch academic interventions for the identified professor
            academic_interventions = get_academic_interventions(professor_id)
            
            if academic_interventions:
                return render_template("professorAddAcad.html", academic_interventions=academic_interventions)
            else:
                return render_template("professorAddAcad.html", no_classes_message=True)
        else:
            flash("Professor information not found.")
            return redirect(url_for("auth.login"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    
@views.route('/professorAddAcadStudents/<int:professor_id>/<string:subj_id>')
def professorAddAcadStudents(professor_id, subj_id):
    if "user_id" in session:
        user_id = session["user_id"]

        # Fetch student predictions based on professor_id and subj_id
        students = get_student_predictions_by_professor_and_subject(professor_id, subj_id)
        
        # Fetch a single existing comment for the professor and subject
        existing_comment = get_existing_comment(professor_id, subj_id)

        # Fetch a single existing link for the professor and subject
        existing_link = get_existing_link(professor_id, subj_id)

        # Fetch subject details for the given subject id
        subject_details = get_subject_details(subj_id)

        return render_template(
            "professorAddAcadStudents.html", 
            students=students,
            existing_comment=existing_comment,
            existing_link=existing_link,  # Pass single comment to the template
            subject_id=subj_id,  
            subject_name=subject_details['SubjectName'] if subject_details else None,
            professor_id=professor_id  
        )
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))

@views.route('/add_academic_requirement', methods=['POST'])
def add_academic_requirement():
    if "user_id" in session:
        user_id = session["user_id"]
        
        # Get data from the form
        professor_id = request.form.get('prof_id')
        subject_id = request.form.get('subj_id')
        comment = request.form.get('comment')
        link = request.form.get('link')

        print(f"Professor ID: {professor_id}, Subject ID: {subject_id}, Link: {link}")  # Debugging line

        # Function to insert or update the academic requirement with the link
        success = add_or_update_academic_requirement(professor_id, subject_id, comment, link)

        if success:
            flash("Academic requirement added/updated successfully!")
            return redirect(url_for('views.professorAddAcadStudents', professor_id=professor_id, subj_id=subject_id))
        else:
            flash("Failed to add/update academic requirement.")
            return redirect(url_for('views.professorAddAcadStudents', professor_id=professor_id, subj_id=subject_id))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))


@views.route('/studentsIntervention')
def studentsIntervention():
    if "user_id" in session:
        user_id = session["user_id"]
        student_id = fetch_student_id(user_id)  # Fetch the StudentID
        
        if student_id is not None:
            # Fetching academic, socioeconomic, and behavioral interventions
            academic_interventions = fetch_academic_interventions(student_id)
            socioeconomic_interventions = fetch_socioeconomic_interventions(student_id)
            behavioral_interventions = fetch_behavioral_interventions(student_id)

            # Debugging output for Heroku logs
            print("Academic Interventions:", academic_interventions)
            print("Socioeconomic Interventions:", socioeconomic_interventions)
            print("Behavioral Interventions:", behavioral_interventions)

            # Render the template with the fetched interventions
            return render_template("studentsIntervention.html", 
                                   student_id=student_id, 
                                   academic_interventions=academic_interventions,
                                   socioeconomic_interventions=socioeconomic_interventions,
                                   behavioral_interventions=behavioral_interventions)
        else:
            flash("No student found for this user.")
            return redirect(url_for("views.studentsHome"))
    else:
        flash("Please login to access this content.")
        return redirect(url_for("auth.login"))
    

@views.route('/add_alerts', methods=['POST'])
def add_alerts():
    connection = connect_to_database()
    if connection is None:
        flash("Database connection error", "error")
        return redirect(url_for("views.studentsHome"))  # Change to an appropriate redirect

    try:
        cursor = connection.cursor()
        
        # Query to fetch students without prediction data
        query = """
            SELECT StudentID 
            FROM students 
            WHERE StudentID NOT IN (SELECT DISTINCT StudentID FROM prediction)
        """
        cursor.execute(query)
        students_without_prediction = cursor.fetchall()

        for student in students_without_prediction:
            student_id = student[0]  # Use index to get StudentID
            
            # Check if an alert already exists for this student
            check_query = "SELECT COUNT(*) FROM alert WHERE StudentID = %s"
            cursor.execute(check_query, (student_id,))
            alert_exists = cursor.fetchone()[0]  # This should return the count
            
            if alert_exists == 0:  # Only insert if no alert exists
                alert_message = "Yes"
                insert_query = "INSERT INTO alert (StudentID, Alert) VALUES (%s, %s)"
                cursor.execute(insert_query, (student_id, alert_message))
        
        connection.commit()
        flash("Alerts added for students without prediction data", "success")
        
    except mysql.connector.Error as err:
        print(f"Error adding alerts: {err}")
        flash("Error adding alerts", "error")
    
    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

    return redirect(url_for("views.adminPrediction"))



    