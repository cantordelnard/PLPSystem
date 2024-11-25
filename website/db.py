import bcrypt
import mysql.connector
import numpy as np

'''
#<!-- =============== DATABASE CONNECTION LOCAL ================ -->
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "onlinegradingsystem1"
}

#<!-- =============== DATABASE CONNECTION HEROKU ================ -->
'''
db_config = {
    "host": "gtizpe105piw2gfq.cbetxkdyhwsb.us-east-1.rds.amazonaws.com",
    "user": "xg67haofud3g5u2l",
    "password": "iln0oyv4l4t0kdyj",
    "database": "fpnzzwqo0h0jrll9"
}

def connect_to_database():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print('Connected to MySQL database')
            return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
def insert_schoolyears(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        for index, row in df.iterrows():
            cursor.execute(""" 
                INSERT INTO schoolyear (SchoolYearID, Year) 
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE 
                    Year = VALUES(Year)
                """, (row['SchoolYearID'], row['Year']))  # Use ID from Excel

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")

    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.close()
        conn.close()

def insert_classes(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        for index, row in df.iterrows():
            cursor.execute(""" 
                INSERT INTO classes (ClassID, ClassName, SchoolYearID) 
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    ClassName = VALUES(ClassName), 
                    SchoolYearID = VALUES(SchoolYearID)
                """, (row['ClassID'], row['ClassName'], row['SchoolYearID']))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")

    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.close()
        conn.close()

def insert_professoradvisory(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        for index, row in df.iterrows():
            cursor.execute(""" 
                INSERT INTO professoradvisory (AdvisoryID, ProfessorID, ClassID, SubjectID, SemesterID) 
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    ProfessorID = VALUES(ProfessorID), 
                    ClassID = VALUES(ClassID), 
                    SubjectID = VALUES(SubjectID), 
                    SemesterID = VALUES(SemesterID)
                """, (row['AdvisoryID'], row['ProfessorID'], row['ClassID'], row['SubjectID'], row['SemesterID']))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {e}")

    finally:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.close()
        conn.close()


def insert_users(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        # Hash the password from the DataFrame
        hashed_password = bcrypt.hashpw(row['Password'].encode('utf-8'), bcrypt.gensalt())
        
        # Insert the user data into the database with the hashed password
        cursor.execute(""" 
            INSERT INTO users (UserID, Username, Password, RoleID) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                Username = VALUES(Username), 
                Password = VALUES(Password), 
                RoleID = VALUES(RoleID)
            """, (row['UserID'], row['Username'], hashed_password, row['RoleID']))
    
    conn.commit()
    cursor.close()
    conn.close()

def insert_admins(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Disable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    # Fetch the current max AdminID
    max_adminid = get_max_adminid() or 0  # If None, start with 0

    for index, row in df.iterrows():
        max_adminid += 1  # Increment the ID
        cursor.execute("""
            INSERT INTO admins (AdminID, UserID, FirstName, LastName, Email) 
            VALUES (%s, %s, %s, %s, %s)
            """, (max_adminid, row['UserID'], row['FirstName'], row['LastName'], row['Email']))

    conn.commit()

    # Enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    cursor.close()
    conn.close()

def get_max_adminid():
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(AdminID) FROM admins")
    max_id = cursor.fetchone()[0]  # Get the first column from the result
    cursor.close()
    conn.close()

    return max_id

def insert_prof(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Disable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    # Fetch the current max ProfessorID
    max_professorid = get_max_professorid() or 0  # If None, start with 0

    for index, row in df.iterrows():
        max_professorid += 1  # Increment the ID
        cursor.execute("""
            INSERT INTO professors (ProfessorID, UserID, FirstName, LastName, Email, ProgramID) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (max_professorid, row['UserID'], row['FirstName'], row['LastName'], row['Email'], row['ProgramID']))

    conn.commit()

    # Enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    cursor.close()
    conn.close()

def get_max_professorid():
    conn = connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(ProfessorID) FROM professors")
    max_id = cursor.fetchone()[0]  # Get the first column from the result
    cursor.close()
    conn.close()

    return max_id


def insert_students(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Disable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    # Replace NaN values with None (which maps to NULL in SQL)
    df = df.replace({np.nan: None})

    for index, row in df.iterrows():
        cursor.execute("""
            INSERT INTO students (StudentID, UserID, FirstName, LastName, ClassID, ProgramID, Email, 
                                  SpecializationID, YearLevelID, Age, Gender, MotherOccupation, 
                                  MotherSalary, FatherOccupation, FatherSalary, NumberOfSiblings, 
                                  SeniorHighSchoolAverage) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            UserID = VALUES(UserID), 
            FirstName = VALUES(FirstName), 
            LastName = VALUES(LastName), 
            ClassID = VALUES(ClassID), 
            ProgramID = VALUES(ProgramID), 
            Email = VALUES(Email), 
            SpecializationID = VALUES(SpecializationID), 
            YearLevelID = VALUES(YearLevelID), 
            Age = VALUES(Age), 
            Gender = VALUES(Gender), 
            MotherOccupation = VALUES(MotherOccupation), 
            MotherSalary = VALUES(MotherSalary), 
            FatherOccupation = VALUES(FatherOccupation), 
            FatherSalary = VALUES(FatherSalary), 
            NumberOfSiblings = VALUES(NumberOfSiblings), 
            SeniorHighSchoolAverage = VALUES(SeniorHighSchoolAverage)
        """, (row['StudentID'], row['UserID'], row['FirstName'], row['LastName'], row['ClassID'], 
              row['ProgramID'], row['Email'], row['SpecializationID'], row['YearLevelID'], 
              row['Age'], row['Gender'], row['MotherOccupation'], row['MotherSalary'], 
              row['FatherOccupation'], row['FatherSalary'], row['NumberOfSiblings'], 
              row['SeniorHighSchoolAverage']))

    conn.commit()

    # Enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    cursor.close()
    conn.close()






#<!-- =============== FETCHING CURRENT USER INFORMATION ================ -->
def get_user(username):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE Username = %s", (username,))
            result = cursor.fetchone()
            connection.close()
            return result
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== LOGIN VALIDATION ================ -->
def validate_login(username, password):
    user = get_user(username)
    if user and bcrypt.checkpw(password.encode('utf-8'), user["Password"].encode('utf-8')):
        return user
    return None


#<!-- =============== FETCHING STUDENTS INFORMATION FOR DASHBOARD ================ -->
def get_student_info(user_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT s.StudentID, CONCAT(s.FirstName, ' ', s.LastName) AS FullName, sp.SpecializationName, yl.YearLevelName
            FROM students s
            LEFT JOIN specializations sp ON s.SpecializationID = sp.SpecializationID
            LEFT JOIN yearlevels yl ON s.YearLevelID = yl.YearLevelID
            WHERE s.UserID = %s
            """
            cursor.execute(query, (user_id,))
            student_info = cursor.fetchone()
            connection.close()
            return student_info
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

def get_student_info_explore(user_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Query to get student information
            query_student = """
            SELECT s.StudentID, CONCAT(s.FirstName, ' ', s.LastName) AS FullName, 
                   sp.SpecializationName, yl.YearLevelName,
                   s.Age, s.Gender, s.NumberOfSiblings, s.MotherOccupation, s.MotherSalary, 
                   s.FatherOccupation, s.FatherSalary, s.SeniorHighSchoolAverage
            FROM students s
            LEFT JOIN specializations sp ON s.SpecializationID = sp.SpecializationID
            LEFT JOIN yearlevels yl ON s.YearLevelID = yl.YearLevelID
            WHERE s.UserID = %s
            """
            cursor.execute(query_student, (user_id,))
            student_info = cursor.fetchone()

            if student_info:
                # Get grades for the student
                query_grades = """
                SELECT g.SubjectID, COALESCE(g.AverageGrade, 0) AS AverageGrade
                FROM grades g
                WHERE g.StudentID = %s
                """
                cursor.execute(query_grades, (student_info['StudentID'],))
                grades = cursor.fetchall()
                
                # Convert the list of grades into a dictionary
                grades_dict = {grade['SubjectID'].strip(): grade for grade in grades}

                # Define all subject IDs to check against
                subject_ids = [
                    'GE 001', 'GE 005', 'GE 006', 'GE 007', 'GEE 001',
                    'COMP 101', 'COMP 102', 'COMP 103', 'GE 003', 'GE 004', 'IT 101'
                ]

                # Fill in missing subjects with default values
                for subject_id in subject_ids:
                    if subject_id not in grades_dict:
                        grades_dict[subject_id] = {'AverageGrade': 0}

                # Compute the average grade for 1st Year College
                total_grade = sum(grade['AverageGrade'] for grade in grades_dict.values())
                count = len(grades_dict)
                average_grade_first_year = total_grade / count if count > 0 else 0

                # Format average_grade_first_year to 2 decimal places
                student_info['AverageGradeFirstYear'] = f"{average_grade_first_year:.2f}"
                
                # Add the grades dictionary to student_info
                student_info['Grades'] = grades_dict

                # Get behavioral factors for the student
                query_behavioral = """
                SELECT bf.StudyHours, bf.StudyStrategies, bf.RegularStudySchedule, bf.AttendanceRate, 
                       bf.ClassParticipation, bf.TimeManagementRating, bf.StudyDeadlinesFrequency, 
                       bf.MotivationLevel, bf.EngagementLevel, bf.StressFrequency, bf.CopingEffectiveness
                FROM behavioral bf
                WHERE bf.StudentID = %s
                """
                cursor.execute(query_behavioral, (student_info['StudentID'],))
                behavioral_factors = cursor.fetchone()

                # Add behavioral factors to student_info
                if behavioral_factors:
                    student_info['BehavioralFactors'] = {
                        'StudyHours': behavioral_factors.get('StudyHours', 'N/A'),
                        'StudyStrategies': behavioral_factors.get('StudyStrategies', 'N/A'),
                        'RegularStudySchedule': 'Yes' if behavioral_factors.get('RegularStudySchedule') else 'No',
                        'AttendanceRate': behavioral_factors.get('AttendanceRate', 'N/A'),
                        'ClassParticipation': behavioral_factors.get('ClassParticipation', 'N/A'),
                        'TimeManagementRating': behavioral_factors.get('TimeManagementRating', 'N/A'),
                        'StudyDeadlinesFrequency': behavioral_factors.get('StudyDeadlinesFrequency', 'N/A'),
                        'MotivationLevel': behavioral_factors.get('MotivationLevel', 'N/A'),
                        'EngagementLevel': behavioral_factors.get('EngagementLevel', 'N/A'),
                        'StressFrequency': behavioral_factors.get('StressFrequency', 'N/A'),
                        'CopingEffectiveness': behavioral_factors.get('CopingEffectiveness', 'N/A')
                    }
                else:
                    # Default values if behavioral factors are not available
                    student_info['BehavioralFactors'] = {
                        'StudyHours': 'N/A',
                        'StudyStrategies': 'N/A',
                        'RegularStudySchedule': 'N/A',
                        'AttendanceRate': 'N/A',
                        'ClassParticipation': 'N/A',
                        'TimeManagementRating': 'N/A',
                        'StudyDeadlinesFrequency': 'N/A',
                        'MotivationLevel': 'N/A',
                        'EngagementLevel': 'N/A',
                        'StressFrequency': 'N/A',
                        'CopingEffectiveness': 'N/A'
                    }

            connection.close()
            return student_info
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

    
def get_student_grades(student_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT DISTINCT g.SubjectID, s.SubjectName, CONCAT(p.FirstName, ' ', p.LastName) AS ProfessorName, c.ClassName,
                   g.MidtermGrade, g.FinalGrade, g.AverageGrade, s.Units, sem.SemesterName
            FROM grades g
            JOIN subjects s ON g.SubjectID = s.SubjectID
            JOIN classes c ON g.ClassID = c.ClassID
            JOIN professors p ON g.ProfessorID = p.ProfessorID
            JOIN professoradvisory pa ON g.ClassID = pa.ClassID
            JOIN semesters sem ON g.SemesterID = sem.SemesterID
            WHERE g.StudentID = %s
            """
            cursor.execute(query, (student_id,))
            student_grades = cursor.fetchall()
            connection.close()
            return student_grades
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


def get_student_grades_archive(student_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT DISTINCT ga.SubjectID_archive AS SubjectID, s.SubjectName,
                   ga.ProfessorName_archive AS ProfessorName, ga.ClassName_archive AS ClassName,
                   ga.MidtermGrade_archive AS MidtermGrade, ga.FinalGrade_archive AS FinalGrade,
                   ga.AverageGrade_archive AS AverageGrade, s.Units, sem.SemesterName, yl.YearLevelName
            FROM grades_archive ga
            JOIN subjects s ON ga.SubjectID_archive = s.SubjectID
            JOIN semesters sem ON ga.SemesterID_archive = sem.SemesterID
            JOIN yearlevels yl ON ga.YearLevelID_archive = yl.YearLevelID
            WHERE ga.StudentID_archive = %s
            """
            cursor.execute(query, (student_id,))
            grades_archive = cursor.fetchall()
            return grades_archive
        except mysql.connector.Error as err:
            return []  # Return an empty list on error
        finally:
            cursor.close()  # Ensure cursor is closed
            connection.close()  # Ensure connection is closed
    else:
        return []  # Return an empty list if connection fails
    

#<!-- =============== FETCHING ADMINS INFORMATION FOR DASHBOARD ================ -->
def get_admin_info(user_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM admins WHERE UserID = %s", (user_id,))
            admin_info = cursor.fetchone()
            connection.close()
            return admin_info
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING PROFESSORS INFORMATION FOR DASHBOARD ================ -->
def get_professors_info(user_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM professors WHERE UserID = %s", (user_id,))
            professors_info = cursor.fetchone()
            connection.close()
            return professors_info
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

#<!-- =============== FETCHING STUDENT LIST (ADMIN/USERS) ================ -->
def get_student_list():
    connection = connect_to_database()
    if connection:
        try:
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
            student_list = cursor.fetchall()
            connection.close()
            return student_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING ADMIN LIST (ADMIN/USERS) ================ -->
def get_admin_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT admins.AdminID, users.Username, admins.FirstName, admins.LastName, admins.Email 
                FROM admins 
                JOIN users ON admins.UserID = users.UserID
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING PROFESSOR LIST (ADMIN/USERS) ================ --> 
def get_professor_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT professors.ProfessorID, users.Username, professors.FirstName, professors.LastName, professors.Email, collegeprograms.ProgramName
                FROM professors 
                JOIN users ON professors.UserID = users.UserID
                JOIN collegeprograms ON professors.ProgramID = collegeprograms.ProgramID
            """
            cursor.execute(query)
            professor_list = cursor.fetchall()
            connection.close()
            return professor_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

#<!-- =============== FETCHING PROGRAM INFORMATION DROPDOWN ================ -->
def get_program_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT ProgramID, ProgramName FROM collegeprograms")
            programs = cursor.fetchall()
            connection.close()
            return programs
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING SPECIALIZATION INFORMATION DROPDOWN ================ -->
def get_specialization_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT SpecializationID, SpecializationName FROM specializations")
            specializations = cursor.fetchall()
            connection.close()
            return specializations
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING CLASS INFORMATION DROPDOWN ================ -->
def get_class_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT ClassID, ClassName FROM classes")
            classes = cursor.fetchall()
            connection.close()
            return classes
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING YEAR LEVEL INFORMATION DROPDOWN ================ -->
def get_year_level_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT YearLevelID, YearLevelName FROM yearlevels")
            year_levels = cursor.fetchall()
            connection.close()
            return year_levels
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

#<!-- =============== FETCHING USER INFORMATION ================ -->
def get_user_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT UserID, Username FROM users")
            year_levels = cursor.fetchall()
            connection.close()
            return year_levels
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

    
#<!-- =============== FETCHING MAX USERID INFORMATION FOR AUTO INCREMENT ================ -->
def get_max_userid():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT MAX(UserID) FROM users")
            max_userid = cursor.fetchone()[0]
            connection.close()
            return max_userid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING MAX ADMINID INFORMATION FOR AUTO INCREMENT ================ -->
def get_max_adminid():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT MAX(AdminID) FROM admins")
            max_adminid = cursor.fetchone()[0]
            connection.close()
            return max_adminid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING MAX PROFID INFORMATION FOR AUTO INCREMENT ================ -->
def get_max_professorid():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT MAX(ProfessorID) FROM professors")
            max_professorid = cursor.fetchone()[0]
            connection.close()
            return max_professorid
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FUNCTION FOR ADDING NEW USERS (ADMIN, PROFESSOR, AND STUDENT) ================ -->
def insert_user(role_id, username, password, first_name, last_name, email, program_id=None, class_id=None, year_level_id=None, specialization_id=None, student_id=None, age=None, gender=None, mother_occupation=None, mother_salary=None, father_occupation=None, father_salary=None, number_of_siblings=None, senior_high_school_average=None):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Hash the password before inserting
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Check if username already exists
            cursor.execute("SELECT UserID FROM users WHERE Username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                print(f"Username '{username}' already exists. Cannot add user.")
                return False  # Return False indicating failure
            
            max_userid = get_max_userid()
            new_userid = max_userid + 1 if max_userid else 24001  # Start from 24001 if table is empty

            # Insert into users table
            cursor.execute("INSERT INTO users (UserID, Username, Password, RoleID) VALUES (%s, %s, %s, %s)",
                           (new_userid, username, hashed_password, role_id))

            role_id = int(role_id)  # Ensure role_id is an integer for comparison

            # Insert into specific role table (admins, professors, students)
            if role_id == 1:  # Admin
                max_adminid = get_max_adminid()
                new_adminid = max_adminid + 1 if max_adminid else 1  # Start from 1 if table is empty
                cursor.execute("INSERT INTO admins (AdminID, UserID, FirstName, LastName, Email) VALUES (%s, %s, %s, %s, %s)",
                               (new_adminid, new_userid, first_name, last_name, email))
            elif role_id == 2:  # Professor
                max_professorid = get_max_professorid()
                new_professorid = max_professorid + 1 if max_professorid else 1  # Start from 1 if table is empty
                cursor.execute("INSERT INTO professors (ProfessorID, UserID, FirstName, LastName, Email, ProgramID) VALUES (%s, %s, %s, %s, %s, %s)",
                               (new_professorid, new_userid, first_name, last_name, email, program_id))
            elif role_id == 3:  # Student
                cursor.execute("""INSERT INTO students (UserID, StudentID, FirstName, LastName, Email, ClassID, YearLevelID, 
                                SpecializationID, ProgramID, Age, Gender, MotherOccupation, MotherSalary, FatherOccupation, 
                                FatherSalary, NumberOfSiblings, SeniorHighSchoolAverage) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                               (new_userid, student_id, first_name, last_name, email, class_id, year_level_id, 
                                specialization_id, program_id, age, gender, mother_occupation, mother_salary, 
                                father_occupation, father_salary, number_of_siblings, senior_high_school_average))

            connection.commit()
            connection.close()
            print("New user added successfully")
            return True  # Return True indicating success
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return False  # Return False on database error
    else:
        print("Failed to connect to the database")
        return False  # Return False on connection failure

    

#<!-- =============== FETCHING SCHOOLYEAR LIST ================ -->
def get_schoolyear_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT schoolyear.SchoolYearID, schoolyear.Year 
                FROM schoolyear 
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    
def archive_schoolyear_data(schoolyear_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()

            # Disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            # Step 4: Archive grades
            cursor.execute(
                "INSERT INTO grades_archive (GradeID_archive, StudentID_archive, SubjectID_archive, "
                "MidtermGrade_archive, FinalGrade_archive, SemesterID_archive, AverageGrade_archive, "
                "ProfessorName_archive, Year_archive, ClassName_archive, YearLevelID_archive) "
                "SELECT g.GradeID, g.StudentID, g.SubjectID, g.MidtermGrade, g.FinalGrade, g.SemesterID, "
                "g.AverageGrade, CONCAT(p.FirstName, ' ', p.LastName) AS ProfessorName, sy.Year, c.ClassName, s.YearLevelID "
                "FROM grades g "
                "JOIN students s ON g.StudentID = s.StudentID "
                "JOIN professors p ON g.ProfessorID = p.ProfessorID "
                "JOIN schoolyear sy ON g.SchoolYearID = sy.SchoolYearID "
                "JOIN classes c ON g.ClassID = c.ClassID "
                "WHERE g.SchoolYearID = %s",
                (schoolyear_id,)
            )
            print("Grades archived.")

            # Step 1: Archive school year
            cursor.execute(
                "INSERT INTO schoolyear_archive (SchoolYearID_archive, Year_archive) "
                "SELECT SchoolYearID, Year FROM schoolyear WHERE SchoolYearID = %s",
                (schoolyear_id,)
            )
            print("School year archived.")

            # Step 2: Archive classes
            cursor.execute(
                "INSERT INTO classes_archive (ClassID_archive, ClassName_archive, SchoolYearID_archive) "
                "SELECT ClassID, ClassName, SchoolYearID FROM classes WHERE SchoolYearID = %s",
                (schoolyear_id,)
            )
            print("Classes archived.")

            # Step 3: Archive professor advisory
            cursor.execute(
                "INSERT INTO professoradvisory_archive (AdvisoryID_archive, ProfessorID_archive, ClassID_archive, SubjectID_archive, SemesterID_archive) "
                "SELECT AdvisoryID, ProfessorID, ClassID, SubjectID, SemesterID FROM professoradvisory "
                "WHERE ClassID IN (SELECT ClassID FROM classes WHERE SchoolYearID = %s)",
                (schoolyear_id,)
            )
            print("Professor advisory archived.")

            # Commit the transaction to save the archived data
            connection.commit()

            # Step 5: Delete original grades
            cursor.execute("DELETE FROM grades WHERE SchoolYearID = %s", (schoolyear_id,))
            connection.commit()  # Commit after deleting grades
            print("Original grades deleted.")

            # Step 6: Delete original professor advisory
            cursor.execute(
                "DELETE FROM professoradvisory WHERE ClassID IN (SELECT ClassID FROM classes WHERE SchoolYearID = %s)",
                (schoolyear_id,)
            )
            connection.commit()  # Commit after deleting professor advisory
            print("Original professor advisory deleted.")

            # Step 7: Delete original classes
            cursor.execute("DELETE FROM classes WHERE SchoolYearID = %s", (schoolyear_id,))
            connection.commit()  # Commit after deleting classes
            print("Original classes deleted.")

            # Step 8: Delete original school year
            cursor.execute("DELETE FROM schoolyear WHERE SchoolYearID = %s", (schoolyear_id,))
            connection.commit()  # Commit after deleting school year
            print("Original school year deleted.")

            # Step 9: Check ClassID in students and update if necessary
            cursor.execute("SELECT ClassID FROM classes;")
            class_ids = cursor.fetchall()  # Fetch all ClassIDs
            class_id_array = [class_id[0] for class_id in class_ids]  # Create a list from the results
            print(f"Available Class IDs: {class_id_array}")

            # Update students' ClassID to 1 if their ClassID is not in the class_id_array
            cursor.execute(
                """
                UPDATE students
                SET ClassID = 0
                WHERE ClassID NOT IN (%s)
                """ % ','.join(map(str, class_id_array))  # Convert array to a comma-separated string
            )
            connection.commit()  # Commit the changes
            print("Updated ClassID of students to 1 for non-existing classes.")

            # Enable foreign key checks back
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            return True  # Return success

        except mysql.connector.Error as err:
            print(f"Error: {err}")  # Print the specific error message
            connection.rollback()  # Rollback in case of error
            return False
        finally:
            connection.close()
    else:
        print("Failed to connect to the database.")
        return False
    
def get_archived_schoolyears():
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM schoolyear_archive")
        archived_years = cursor.fetchall()
        connection.close()
        return archived_years
    return []



    
#<!-- =============== FETCHING PROGRAM LIST ================ -->
def get_program_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT collegeprograms.ProgramID, collegeprograms.ProgramName
                FROM collegeprograms 
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING SPCECIALIZATION LIST ================ -->
def get_specialization_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT specializations.SpecializationID, specializations.SpecializationName, collegeprograms.ProgramName
                FROM specializations
                JOIN collegeprograms ON specializations.ProgramID = collegeprograms.ProgramID
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

#<!-- =============== FETCHING SUBJECT LIST ================ -->
def get_subject_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT subjects.SubjectID, subjects.SubjectName, subjects.Units, collegeprograms.ProgramName
                FROM subjects
                JOIN collegeprograms ON subjects.ProgramID = collegeprograms.ProgramID
            """
            cursor.execute(query)
            subject_list = cursor.fetchall()
            print(f"Subjects fetched from DB: {subject_list}")  # Debug print
            connection.close()
            return subject_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


#<!-- =============== FETCHING CLASSES LIST ================ -->
def get_classes_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT classes.ClassID, classes.ClassName, schoolyear.Year
                FROM classes
                JOIN schoolyear ON classes.SchoolYearID = schoolyear.SchoolYearID
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

#<!-- =============== FETCHING PROFESSOR ADVISORY LIST ================ -->
def get_professoradvisory_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT professoradvisory.AdvisoryID, professors.FirstName, professors.LastName, classes.ClassName, subjects.SubjectName, semesters.SemesterName
                FROM professoradvisory
                JOIN professors ON professoradvisory.ProfessorID = professors.ProfessorID
                JOIN classes ON professoradvisory.ClassID = classes.ClassID
                JOIN subjects ON professoradvisory.SubjectID = subjects.SubjectID
                JOIN semesters ON professoradvisory.SemesterID = semesters.SemesterID
            """
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None


def get_semesters_list():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """SELECT SemesterID, SemesterName FROM semesters"""
            cursor.execute(query)
            admin_list = cursor.fetchall()
            connection.close()
            return admin_list
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

def check_duplicate_entry(table, column, value):
    conn = connect_to_database()
    cursor = conn.cursor()
    try:
        query = f"SELECT 1 FROM {table} WHERE {column} = %s LIMIT 1"
        cursor.execute(query, (value,))
        result = cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        result = None
    finally:
        cursor.close()
        conn.close()
    
    return result is not None


def add_schoolyear(schoolyearid, year):
    if check_duplicate_entry('schoolyear', 'SchoolYearID', schoolyearid):
        return False, 'SchoolYearID already exists.'
    if check_duplicate_entry('schoolyear', 'Year', year):
        return False, 'Year already exists.'

    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO schoolyear (SchoolYearID, Year) VALUES (%s, %s)", (schoolyearid, year))
    conn.commit()
    cursor.close()
    conn.close()
    return True, 'School year added successfully!'


def add_program(program_id, program_name):
    if check_duplicate_entry('collegeprograms', 'ProgramID', program_id):
        return False, 'ProgramID already exists.'
    if check_duplicate_entry('collegeprograms', 'ProgramName', program_name):
        return False, 'ProgramName already exists.'

    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO collegeprograms (ProgramID, ProgramName) VALUES (%s, %s)", (program_id, program_name))
    conn.commit()
    cursor.close()
    conn.close()
    return True, 'Program added successfully!'


def add_specialization(specialization_id, specialization_name, program_name):
    if check_duplicate_entry('specializations', 'SpecializationID', specialization_id):
        return False, 'SpecializationID already exists.'
    if check_duplicate_entry('specializations', 'SpecializationName', specialization_name):
        return False, 'SpecializationName already exists.'

    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO specializations (SpecializationID, SpecializationName, ProgramID) VALUES (%s, %s, %s)",
        (specialization_id, specialization_name, program_name)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, 'Specialization added successfully!'


def add_subject(subject_id, subject_name, subject_units, subject_program_name):
    if check_duplicate_entry('subjects', 'SubjectID', subject_id):
        return False, 'SubjectID already exists.'
    if check_duplicate_entry('subjects', 'SubjectName', subject_name):
        return False, 'SubjectName already exists.'

    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subjects (SubjectID, SubjectName, Units, ProgramID) VALUES (%s, %s, %s, %s)",
        (subject_id, subject_name, subject_units, subject_program_name)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, 'Subject added successfully!'


def add_class(class_id, class_name, class_year):
    if check_duplicate_entry('classes', 'ClassID', class_id):
        return False, 'ClassID already exists.'
    if check_duplicate_entry('classes', 'ClassName', class_name):
        return False, 'ClassName already exists.'

    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO classes (ClassID, ClassName, SchoolYearID) VALUES (%s, %s, %s)",
        (class_id, class_name, class_year)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, 'Class added successfully!'


def add_professoradvisory(advisory_id, professor_id, class_id, subject_id, semester_id):
    # Check if AdvisoryID already exists
    if check_duplicate_entry('professoradvisory', 'AdvisoryID', advisory_id):
        return False  # Indicate that the AdvisoryID already exists

    # Check if there is already an advisory assignment for the given professor, class, subject, and semester
    if check_duplicate_entry('professoradvisory', 'ProfessorID', professor_id) and \
       check_duplicate_entry('professoradvisory', 'ClassID', class_id) and \
       check_duplicate_entry('professoradvisory', 'SubjectID', subject_id) and \
       check_duplicate_entry('professoradvisory', 'SemesterID', semester_id):
        return False  # Indicate that a duplicate advisory assignment was found

    # If no duplicates were found, proceed with the insertion
    conn = connect_to_database()
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO professoradvisory (AdvisoryID, ProfessorID, ClassID, SubjectID, SemesterID)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (advisory_id, professor_id, class_id, subject_id, semester_id))
    conn.commit()

    cursor.close()
    conn.close()
    return True  # Indicate that the insertion was successful



def get_schoolyear_by_id(schoolyear_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM schoolyear WHERE SchoolYearID = %s", (schoolyear_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_program_by_id(program_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM collegeprograms WHERE ProgramID = %s", (program_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_specialization_by_id(specialization_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM specializations WHERE SpecializationID = %s", (specialization_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_subject_by_id(subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT subjects.SubjectID, subjects.SubjectName, subjects.Units, subjects.ProgramID, collegeprograms.ProgramName
                FROM subjects
                JOIN collegeprograms ON subjects.ProgramID = collegeprograms.ProgramID
                WHERE subjects.SubjectID = %s
            """
            cursor.execute(query, (subject_id,))
            subject = cursor.fetchone()
            connection.close()
            return subject
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

def get_class_by_id(class_id):
    conn = connect_to_database()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT classes.ClassID, classes.ClassName, classes.SchoolYearID, schoolyear.Year
        FROM classes
        JOIN schoolyear ON classes.SchoolYearID = schoolyear.SchoolYearID
        WHERE ClassID = %s
    """
    cursor.execute(query, (class_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_professoradvisory_by_id(advisory_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT pa.AdvisoryID, pa.ProfessorID, p.FirstName, p.LastName, pa.ClassID, pa.SubjectID, pa.SemesterID
                FROM professoradvisory pa
                JOIN professors p ON pa.ProfessorID = p.ProfessorID
                WHERE pa.AdvisoryID = %s
            """
            cursor.execute(query, (advisory_id,))
            advisory_data = cursor.fetchone()
            connection.close()
            print("Advisory Data:", advisory_data)  # Debug print
            return advisory_data
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

def update_schoolyear(school_year_id, year):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Check if the year already exists in the database
        check_query = "SELECT 1 FROM schoolyear WHERE Year = %s AND SchoolYearID != %s"
        cursor.execute(check_query, (year, school_year_id))
        result = cursor.fetchone()
        
        if result:
            # Duplicate found, return a message indicating failure
            raise ValueError("This school year already exists.")
        
        # If no duplicate found, proceed with the update
        query = "UPDATE schoolyear SET Year = %s WHERE SchoolYearID = %s"
        cursor.execute(query, (year, school_year_id))
        conn.commit()
        print(f"Updated school year {school_year_id} to {year}")
        
    except mysql.connector.Error as err:
        print(f"Error updating school year: {err}")
        raise  # Re-raise the error to be caught by the view function
    except ValueError as ve:
        raise ve  # Raise the custom ValueError for duplicate detection
    finally:
        cursor.close()
        conn.close()

def update_program_db(program_id, program_name):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Check if the program name already exists in the database (excluding the current program)
        check_query = "SELECT 1 FROM collegeprograms WHERE ProgramName = %s AND ProgramID != %s"
        cursor.execute(check_query, (program_name, program_id))
        result = cursor.fetchone()
        
        if result:
            # If the program name already exists, raise a ValueError for duplicate entry
            raise ValueError("This program name already exists.")
        
        # If no duplicate found, proceed with the update
        query = "UPDATE collegeprograms SET ProgramName = %s WHERE ProgramID = %s"
        cursor.execute(query, (program_name, program_id))
        conn.commit()
        print(f"Updated program {program_id} to {program_name}")
        
    except mysql.connector.Error as err:
        print(f"Error updating program: {err}")
        raise  # Re-raise the error to be caught by the view function
    except ValueError as ve:
        raise ve  # Raise the custom ValueError for duplicate detection
    finally:
        cursor.close()
        conn.close()

def update_specialization_db(specialization_id, specialization_name, program_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Check if the specialization name already exists in the program (excluding the current specialization)
        check_query = """
            SELECT 1 FROM specializations
            WHERE SpecializationName = %s AND ProgramID = %s AND SpecializationID != %s
        """
        cursor.execute(check_query, (specialization_name, program_id, specialization_id))
        result = cursor.fetchone()
        
        if result:
            # If the specialization name already exists within the same program, raise an error
            raise ValueError("This specialization name already exists for the selected program.")
        
        # If no duplicate is found, proceed with the update
        query = "UPDATE specializations SET SpecializationName = %s, ProgramID = %s WHERE SpecializationID = %s"
        cursor.execute(query, (specialization_name, program_id, specialization_id))
        conn.commit()
        print(f"Updated specialization {specialization_id} to {specialization_name} for program {program_id}")
        
    except mysql.connector.Error as err:
        print(f"Error updating specialization: {err}")
        raise  # Re-raise the error to be caught by the view function
    except ValueError as ve:
        raise ve  # Raise the custom ValueError for duplicate detection
    finally:
        cursor.close()
        conn.close()



def update_subject_db(subject_id, subject_name, subject_units, program_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    
    try:
        # Check if the subject name already exists in the program (excluding the current subject being updated)
        check_query = """
            SELECT 1 FROM subjects
            WHERE SubjectName = %s AND ProgramID = %s AND SubjectID != %s
        """
        cursor.execute(check_query, (subject_name, program_id, subject_id))
        result = cursor.fetchone()
        
        if result:
            # If the subject name already exists within the same program, raise an error
            raise ValueError("This subject name already exists for the selected program.")
        
        # If no duplicate is found, proceed with the update
        query = """
            UPDATE subjects
            SET SubjectName = %s, Units = %s, ProgramID = %s
            WHERE SubjectID = %s
        """
        cursor.execute(query, (subject_name, subject_units, program_id, subject_id))
        conn.commit()
        print(f"Updated subject {subject_id} to {subject_name} for program {program_id}")
        
    except mysql.connector.Error as err:
        print(f"Error updating subject: {err}")
        raise  # Re-raise the error to be caught by the view function
    except ValueError as ve:
        raise ve  # Raise the custom ValueError for duplicate detection
    finally:
        cursor.close()
        conn.close()

def update_class_db(class_id, class_name, schoolyear_id):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Check if a class with the same name already exists in the selected school year (excluding the class being updated)
        check_query = """
            SELECT 1 FROM classes 
            WHERE ClassName = %s AND SchoolYearID = %s AND ClassID != %s
        """
        cursor.execute(check_query, (class_name, schoolyear_id, class_id))
        result = cursor.fetchone()

        if result:
            # If the class name already exists in the selected school year, raise an error
            raise ValueError("This class name already exists for the selected school year.")
        
        # Proceed with the class update if no duplicate is found
        query = "UPDATE classes SET ClassName = %s, SchoolYearID = %s WHERE ClassID = %s"
        cursor.execute(query, (class_name, schoolyear_id, class_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Updated class {class_id} to {class_name}, year {schoolyear_id}")
        else:
            print(f"No rows updated for class {class_id}")
    
    except mysql.connector.Error as err:
        print(f"Error updating class: {err}")
        raise  # Re-raise the error to be caught in the view function
    except ValueError as ve:
        raise ve  # Raise the custom ValueError for duplicate detection
    finally:
        cursor.close()
        conn.close()

def update_professoradvisory_db(advisory_id, professor_id, class_id, subject_id, semester_id):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        # Check if a professor is already assigned to the same subject in the same class
        check_query = """
            SELECT 1 FROM professoradvisory
            WHERE ClassID = %s AND SubjectID = %s AND AdvisoryID != %s
        """
        cursor.execute(check_query, (class_id, subject_id, advisory_id))
        result = cursor.fetchone()

        if result:
            # If there is an existing professor advisory for the same class and subject, raise an error
            raise ValueError("This class already has a professor assigned for the selected subject.")

        # Proceed with updating the professor advisory
        query = """
            UPDATE professoradvisory 
            SET ProfessorID = %s, ClassID = %s, SubjectID = %s, SemesterID = %s 
            WHERE AdvisoryID = %s
        """
        cursor.execute(query, (professor_id, class_id, subject_id, semester_id, advisory_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Updated professor advisory {advisory_id} for professor {professor_id}, class {class_id}, subject {subject_id}, semester {semester_id}")
        else:
            print(f"No rows updated for professor advisory {advisory_id}")

    except mysql.connector.Error as err:
        print(f"Error updating professor advisory: {err}")
        conn.rollback()
        raise
    except ValueError as ve:
        raise ve  # Raise the custom error for duplicate advisory detection
    finally:
        cursor.close()
        conn.close()









def get_professors_advisory_classes(professor_id):
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT pa.ClassID, c.ClassName
            FROM professoradvisory pa
            JOIN classes c ON pa.ClassID = c.ClassID
            WHERE pa.ProfessorID = %s
        """
        cursor.execute(query, (professor_id,))
        advisory_classes = cursor.fetchall()
        connection.close()
        return advisory_classes
    return None

def get_professor_classes_subjects(professor_id):
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT c.ClassID, c.ClassName, s.SubjectID, s.SubjectName
            FROM professoradvisory pa
            JOIN classes c ON pa.ClassID = c.ClassID
            JOIN subjects s ON pa.SubjectID = s.SubjectID
            WHERE pa.ProfessorID = %s
        """
        cursor.execute(query, (professor_id,))
        classes_subjects = cursor.fetchall()
        connection.close()
        return classes_subjects
    return None



def get_students_by_class(class_id, subject_id):
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT DISTINCT s.StudentID, s.FirstName, s.LastName, c.ClassName, sub.SubjectName, sem.SemesterName, c.SchoolYearID, sem.SemesterID,
                            g.MidtermGrade, g.FinalGrade
            FROM students s
            JOIN classes c ON s.ClassID = c.ClassID
            JOIN professoradvisory pa ON c.ClassID = pa.ClassID
            JOIN subjects sub ON pa.SubjectID = sub.SubjectID
            JOIN semesters sem ON pa.SemesterID = sem.SemesterID
            LEFT JOIN grades g ON s.StudentID = g.StudentID AND sub.SubjectID = g.SubjectID AND c.ClassID = g.ClassID
            WHERE s.ClassID = %s AND sub.SubjectID = %s
        """
        cursor.execute(query, (class_id, subject_id))
        result = cursor.fetchall()
        connection.close()
        return result
    return None



# Function to fetch ProfessorID based on UserID
def get_professor_id_by_user_id(user_id):
    connection = connect_to_database()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT ProfessorID FROM professors WHERE UserID = %s"
        cursor.execute(query, (user_id,))
        professor = cursor.fetchone()
        connection.close()
        if professor:
            return professor['ProfessorID']
        else:
            return None
    else:
        return None


# Fetching the count of students
def get_student_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM students")
            student_count = cursor.fetchone()['count']
            connection.close()
            return student_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

# Fetching the count of professors
def get_professor_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM professors")
            professor_count = cursor.fetchone()['count']
            connection.close()
            return professor_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

# Fetching the count of admins
def get_admin_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM admins")
            admin_count = cursor.fetchone()['count']
            connection.close()
            return admin_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

# Fetching the count of subjects
def get_subject_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM subjects")
            subject_count = cursor.fetchone()['count']
            connection.close()
            return subject_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    
def get_average_percentage(student_id):
    # Connect to the database
    connection = connect_to_database()
    average_percentage = None

    if connection:
        try:
            cursor = connection.cursor()

            # Query to get the average percentage for the specific student
            query = """
            SELECT AveragePercentage FROM behavioral
            WHERE StudentID = %s
            """
            cursor.execute(query, (student_id,))  # Pass student_id for filtering
            result = cursor.fetchone()

            # Check if we got a result
            if result and result[0] is not None:
                average_percentage = result[0]
            else:
                average_percentage = 0.0  # Default if no data found

            cursor.close()
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            connection.close()

    return average_percentage

def get_student_predictions():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT 
                s.StudentID,
                CONCAT(s.FirstName, ' ', s.LastName) AS FullName,
                p.Prediction AS Percentage,
                p.Remarks,
                p.interventionTag
            FROM 
                students s
            LEFT JOIN 
                prediction p ON s.StudentID = p.StudentID
            """
            cursor.execute(query)
            student_predictions = cursor.fetchall()
            connection.close()
            return student_predictions
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None
    
# Function 1: Fetch students with academic risk based on FactorID and remarks.
def get_academic_risk_students():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT 
                s.StudentID, 
                CONCAT(s.FirstName, ' ', s.LastName) AS FullName,
                p.Prediction AS Percentage,
                p.Remarks,
                p.FactorID
            FROM 
                students s
            LEFT JOIN 
                prediction p ON s.StudentID = p.StudentID
            WHERE 
                p.Remarks = 'WILL NOT GRADUATE ON TIME'
            """
            cursor.execute(query)
            academic_risk_students = cursor.fetchall()
            connection.close()
            return academic_risk_students
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None


# Function 2: Log academic interventions for low grades in IT101 and COMP103.
def log_academic_intervention(academic_students):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            for student in academic_students:
                student_id = student['StudentID']
                
                # Query to check for low grades in specific subjects
                grade_query = """
                SELECT g.SubjectID, g.AverageGrade, g.ProfessorID
                FROM grades g
                WHERE g.StudentID = %s 
                AND g.SubjectID IN ('IT 101', 'COMP 103') 
                AND g.AverageGrade <= 85.49
                """
                cursor.execute(grade_query, (student_id,))
                low_grades = cursor.fetchall()

                for grade in low_grades:
                    # Check for duplicate entry in academicIntervention
                    check_query = """
                    SELECT COUNT(*) FROM academicintervention
                    WHERE ProfID = %s AND SubjID = %s AND StudID = %s
                    """
                    cursor.execute(check_query, (grade['ProfessorID'], grade['SubjectID'], student_id))
                    if cursor.fetchone()['COUNT(*)'] == 0:
                        # Insert intervention record if no duplicate is found
                        insert_query = """
                        INSERT INTO academicintervention (ProfID, SubjID, StudID, Comment)
                        VALUES (%s, %s, %s, %s)
                        """
                        cursor.execute(insert_query, (grade['ProfessorID'], grade['SubjectID'], student_id, ""))

                    else:
                        print(f"Duplicate entry detected for StudentID {student_id}, SubjectID {grade['SubjectID']}")
            
            # Commit changes for academic interventions
            connection.commit()
            print("Academic Interventions Logged.")

            # Update interventionTag to 'Yes' in the prediction table for relevant students
            update_query = """
            UPDATE prediction
            SET interventionTag = 'Yes'
            WHERE StudentID = %s
            AND Remarks IN ('AT RISK', 'NEEDS INTERVENTION')
            """
            for student in academic_students:
                cursor.execute(update_query, (student['StudentID'],))
            
            # Commit updates for interventionTag in prediction table
            connection.commit()
            print("Prediction table updated with interventionTag for academic students.")

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.rollback()
        finally:
            connection.close()

    

def insert_socioeconomic_interventions(socioeconomic_students):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Fetch all events for FactorID 1; if not found, use EventID 0 as default
            cursor.execute("SELECT EventID FROM theevents WHERE FactorID = 1")
            events = cursor.fetchall() or [{'EventID': 0}]  # Default to EventID 0 if no events found

            for event in events:  # Loop through each event or default
                event_id = event['EventID']

                for student in socioeconomic_students:
                    # Check if entry already exists for this student and event
                    check_query = """
                    SELECT COUNT(*) AS count FROM socioeconomicintervention
                    WHERE StudID = %s AND EventID = %s
                    """
                    cursor.execute(check_query, (student['StudentID'], event_id))
                    result = cursor.fetchone()

                    # Insert only if the record does not exist
                    if result['count'] == 0:
                        insert_query = """
                        INSERT INTO socioeconomicintervention (StudID, EventID)
                        VALUES (%s, %s)
                        """
                        cursor.execute(insert_query, (student['StudentID'], event_id))

            # Commit intervention records
            connection.commit()
            print("Socioeconomic Interventions Logged.")

            # Update the interventionTag in prediction table for 'WILL NOT GRADUATE ON TIME' remarks
            update_query = """
            UPDATE prediction
            SET interventionTag = 'Yes'
            WHERE StudentID = %s
            AND Remarks = 'WILL NOT GRADUATE ON TIME'
            """
            for student in socioeconomic_students:
                cursor.execute(update_query, (student['StudentID'],))
            
            # Commit updates
            connection.commit()
            print("Prediction table updated with interventionTag for socioeconomic students.")

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.rollback()
        finally:
            connection.close()

def insert_behavioral_interventions(behavioral_students):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)

            # Fetch all events for FactorID 3; if not found, use EventID 0 as default
            cursor.execute("SELECT EventID FROM theevents WHERE FactorID = 3")
            events = cursor.fetchall() or [{'EventID': 0}]  # Default to EventID 0 if no events found

            for event in events:  # Loop through each event or default
                event_id = event['EventID']

                for student in behavioral_students:
                    # Check if entry already exists for this student and event
                    check_query = """
                    SELECT COUNT(*) AS count FROM behavioralintervention
                    WHERE StudID = %s AND EventID = %s
                    """
                    cursor.execute(check_query, (student['StudentID'], event_id))
                    result = cursor.fetchone()

                    # Insert only if the record does not exist
                    if result['count'] == 0:
                        insert_query = """
                        INSERT INTO behavioralintervention (StudID, EventID)
                        VALUES (%s, %s)
                        """
                        cursor.execute(insert_query, (student['StudentID'], event_id))

            # Commit intervention records
            connection.commit()
            print("Behavioral Interventions Logged.")

            # Update the interventionTag in prediction table for 'WILL NOT GRADUATE ON TIME' remarks
            update_query = """
            UPDATE prediction
            SET interventionTag = 'Yes'
            WHERE StudentID = %s
            AND Remarks = 'WILL NOT GRADUATE ON TIME'
            """
            for student in behavioral_students:
                cursor.execute(update_query, (student['StudentID'],))
            
            # Commit updates
            connection.commit()
            print("Prediction table updated with interventionTag for behavioral students.")

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.rollback()
        finally:
            connection.close()
    

def get_academic_interventions(professor_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT 
                ai.ProfID,
                ai.SubjID,
                s.SubjectName,
                MAX(ai.Comment) AS Comment
            FROM 
                academicintervention ai
            JOIN 
                subjects s ON ai.SubjID = s.SubjectID
            WHERE 
                ai.ProfID = %s
            GROUP BY 
                ai.ProfID, ai.SubjID, s.SubjectName
            """
            cursor.execute(query, (professor_id,))
            interventions = cursor.fetchall()
            connection.close()
            return interventions
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None
    

def perform_intervention_based_on_factor():
    all_students = get_academic_risk_students()
    if not all_students:
        print("No students at risk.")
        return

    # Group students by FactorID
    socioeconomic_students = [s for s in all_students if s['FactorID'] in (1, 4, 5, 7)]
    academic_students = [s for s in all_students if s['FactorID'] in (2, 4, 6, 7)]
    behavioral_students = [s for s in all_students if s['FactorID'] in (3, 5, 6, 7)]

    # Perform interventions based on the groups
    if socioeconomic_students:
        insert_socioeconomic_interventions(socioeconomic_students)
    if academic_students:
        log_academic_intervention(academic_students)
    if behavioral_students:
        insert_behavioral_interventions(behavioral_students)

    print("Interventions Successfully Logged.")

    

def get_subject_info(subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT SubjID, SubjectName
                FROM subjects
                WHERE SubjID = %s
            """
            cursor.execute(query, (subject_id,))
            subject_info = cursor.fetchone()
            connection.close()
            return subject_info
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
        
def get_student_predictions_by_intervention(professor_id, subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT 
                    s.StudentID,
                    CONCAT(s.FirstName, ' ', s.LastName) AS FullName,
                    p.Prediction AS Percentage,
                    p.Remarks
                FROM 
                    students s
                LEFT JOIN 
                    prediction p ON s.StudentID = p.StudentID
                JOIN 
                    academicintervention ai ON ai.StudID = s.StudentID
                WHERE 
                    ai.ProfID = %s AND ai.SubjID = %s
            """
            cursor.execute(query, (professor_id, subject_id))
            student_predictions = cursor.fetchall()
            print("Fetched predictions:", student_predictions)  # Debugging statement
            connection.close()
            return student_predictions
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None
    
def get_student_predictions_by_professor_and_subject(professor_id, subj_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT 
                s.StudentID,
                CONCAT(s.FirstName, ' ', s.LastName) AS FullName,
                p.Prediction AS Percentage
            FROM 
                students s
            LEFT JOIN 
                prediction p ON s.StudentID = p.StudentID
            LEFT JOIN 
                academicintervention ai ON s.StudentID = ai.StudID
            WHERE 
                ai.ProfID = %s AND ai.SubjID = %s
            """
            cursor.execute(query, (professor_id, subj_id))
            student_predictions = cursor.fetchall()
            connection.close()
            return student_predictions
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None

def get_subject_details(subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT 
                SubjectID,
                SubjectName
            FROM 
                subjects
            WHERE 
                SubjectID = %s
            """
            cursor.execute(query, (subject_id,))
            subject = cursor.fetchone()
            connection.close()
            return subject
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return None
    else:
        return None
    

def get_all_student_ids_for_professor_subject(professor_id, subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            # Query to get all unique student IDs under the specified professor and subject
            student_query = """
            SELECT DISTINCT StudID 
            FROM academicintervention 
            WHERE ProfID = %s AND SubjID = %s
            """
            cursor.execute(student_query, (professor_id, subject_id))
            students = cursor.fetchall()
            connection.close()
            
            # Extract StudID values from the results and return them as a list
            student_ids = [student['StudID'] for student in students]
            return student_ids
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.close()
            return []
    else:
        return []
    

def get_existing_comment(professor_id, subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT Comment FROM academicintervention 
            WHERE ProfID = %s AND SubjID = %s LIMIT 1
            """
            cursor.execute(query, (professor_id, subject_id))
            result = cursor.fetchone()
            return result['Comment'] if result else ""
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return ""
        finally:
            connection.close()
    return ""
    
def get_existing_link(professor_id, subject_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT Link FROM academicintervention 
            WHERE ProfID = %s AND SubjID = %s LIMIT 1
            """
            cursor.execute(query, (professor_id, subject_id))
            result = cursor.fetchone()
            return result['Link'] if result else ""
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return ""
        finally:
            connection.close()
    return ""

def add_or_update_academic_requirement(professor_id, subject_id, comment, link):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Fetch all students for the given professor and subject
            all_student_ids = get_all_student_ids_for_professor_subject(professor_id, subject_id)

            for stud_id in all_student_ids:
                # Check if an academic intervention record already exists
                check_query = """
                SELECT COUNT(*) AS count FROM academicintervention 
                WHERE ProfID = %s AND SubjID = %s AND StudID = %s
                """
                cursor.execute(check_query, (professor_id, subject_id, stud_id))
                record_exists = cursor.fetchone()['count'] > 0

                if record_exists:
                    # Update existing record
                    update_query = """
                    UPDATE academicintervention 
                    SET Comment = %s, Link = %s
                    WHERE ProfID = %s AND SubjID = %s AND StudID = %s
                    """
                    cursor.execute(update_query, (comment, link, professor_id, subject_id, stud_id))
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO academicintervention (ProfID, SubjID, StudID, Comment, Link) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (professor_id, subject_id, stud_id, comment, link))

                # **Update the interventionTag in the prediction table**
                update_tag_query = """
                UPDATE prediction 
                SET interventionTag = 'Yes'
                WHERE StudentID = %s AND Remarks = 'WILL NOT GRADUATE ON TIME'
                """
                cursor.execute(update_tag_query, (stud_id,))

            connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            connection.rollback()
            return False
        finally:
            connection.close()
    return False


def fetch_student_id(user_id):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT StudentID FROM students WHERE UserID = %s;", (user_id,))
        student_id = cursor.fetchone()  # Fetch the first result
        
        if student_id is not None:
            return student_id[0]  # Return the StudentID
        else:
            return None  # No matching student found

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def fetch_academic_interventions(student_id):
    connection = connect_to_database()
    if connection is None:
        print("Database connection failed")  # Added error log for connection issues
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                ai.AcadIntID,
                CONCAT(p.FirstName, ' ', p.LastName) AS ProfessorName,
                s.SubjectName,
                ai.Comment,
                ai.Link  -- Fetch the Link from academic intervention
            FROM 
                academicintervention ai
            JOIN 
                professors p ON ai.ProfID = p.ProfessorID
            JOIN 
                subjects s ON ai.SubjID = s.SubjectID
            WHERE 
                ai.StudID = %s;
        """, (student_id,))
        
        interventions = cursor.fetchall()  # Fetch all results
        print("Fetched Academic Interventions:", interventions)  # Debug output
        return interventions  # Return the list of interventions

    except mysql.connector.Error as err:
        print(f"Error: {err}")  # Print the error if any issues occur
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_socioeconomic_interventions(student_id):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                e.EventID,
                e.Title,
                e.Description,
                e.Location,
                e.Date,
                e.Time,
                e.Picture,
                e.Link
            FROM 
                socioeconomicintervention si
            JOIN 
                theevents e ON si.EventID = e.EventID
            WHERE 
                si.StudID = %s;
        """, (student_id,))
        
        interventions = cursor.fetchall()  # Fetch all results
        return interventions  # Return the list of interventions

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_behavioral_interventions(student_id):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                e.EventID,
                e.Title,
                e.Description,
                e.Location,
                e.Date,
                e.Time,
                e.Picture,
                e.Link
            FROM 
                behavioralintervention bi
            JOIN 
                theevents e ON bi.EventID = e.EventID
            WHERE 
                bi.StudID = %s;
        """, (student_id,))
        
        interventions = cursor.fetchall()  # Fetch all results
        return interventions  # Return the list of interventions

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fetch_prediction(student_id):
    connection = connect_to_database()
    if connection is None:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT Remarks FROM prediction WHERE StudentID = %s;", (student_id,))
        prediction = cursor.fetchone()  # Fetch the first result
        
        if prediction is not None:
            return prediction[0]  # Return the Remarks
        else:
            return None  # No matching prediction found

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def sign_up(role_id, username, password):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor()

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Check if username already exists
            cursor.execute("SELECT UserID FROM users WHERE Username = %s", (username,))
            existing_user = cursor.fetchone()
            if existing_user:
                print(f"Username '{username}' already exists. Cannot add user.")
                return False  # Return False indicating failure
            
            # Insert into users table
            cursor.execute("INSERT INTO users (Username, Password, RoleID) VALUES (%s, %s, %s)",
                           (username, hashed_password, role_id))

            connection.commit()
            print("New user added successfully")
            return True  # Return True indicating success
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False  # Return False on database error
        finally:
            cursor.close()
            connection.close()
    else:
        print("Failed to connect to the database")
        return False  # Return False on connection failure
    
def fetch_alerts(student_id):
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT Alert FROM alert WHERE StudentID = %s"
            cursor.execute(query, (student_id,))
            alerts = cursor.fetchall()  # Fetch all alerts
            return alerts  # This will be a list of alert dictionaries
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return []
        finally:
            cursor.close()
            connection.close()
    else:
        return []

def get_graduation_status_counts():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN p.Remarks = 'GRADUATE ON TIME' THEN 1 ELSE 0 END) AS on_time,
                    SUM(CASE WHEN p.Remarks = 'WILL NOT GRADUATE ON TIME' THEN 1 ELSE 0 END) AS not_on_time,
                    SUM(CASE WHEN p.Remarks IS NULL THEN 1 ELSE 0 END) AS not_predicted
                FROM students s
                LEFT JOIN prediction p ON s.StudentID = p.StudentID
            """)
            counts = cursor.fetchone()
            connection.close()
            return counts
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

def get_factor_influence_counts():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN FactorID IN (1, 4, 5, 7) THEN 1 ELSE 0 END) AS Socioeconomic_Count,
                    SUM(CASE WHEN FactorID IN (2, 4, 6, 7) THEN 1 ELSE 0 END) AS Academic_Count,
                    SUM(CASE WHEN FactorID IN (3, 5, 6, 7) THEN 1 ELSE 0 END) AS Behavioral_Count
                FROM prediction
                WHERE Remarks = 'WILL NOT GRADUATE ON TIME'
            """)
            counts = cursor.fetchone()
            connection.close()
            # Convert to a list of dictionaries for the frontend
            return [
                {"FactorName": "Socioeconomic", "FactorCount": counts['Socioeconomic_Count']},
                {"FactorName": "Academic", "FactorCount": counts['Academic_Count']},
                {"FactorName": "Behavioral", "FactorCount": counts['Behavioral_Count']}
            ]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

def get_student_at_risk():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    p.StudentID, 
                    s.FirstName, 
                    s.LastName, 
                    p.Prediction AS Percentage,
                    f.FactorName AS Factor,
                    p.InterventionTag AS Intervention
                FROM prediction p
                JOIN students s ON p.StudentID = s.StudentID
                JOIN factor f ON p.FactorID = f.FactorId
                WHERE p.Remarks = 'WILL NOT GRADUATE ON TIME'
            """)
            students_at_risk = cursor.fetchall()
            connection.close()
            
            # Transform data for the carousel format expected by the frontend
            return [
                {
                    "id": student["StudentID"],
                    "name": f"{student['FirstName']} {student['LastName']}",
                    "percentage": f"{student['Percentage']}%",
                    "factor": student["Factor"],
                    "intervention": student["Intervention"]
                }
                for student in students_at_risk
            ]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None

def get_students_graduating_on_time():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    p.StudentID, 
                    s.FirstName, 
                    s.LastName, 
                    p.Prediction AS Percentage
                FROM prediction p
                JOIN students s ON p.StudentID = s.StudentID
                WHERE p.Remarks = 'GRADUATE ON TIME'
            """)
            students_graduating_on_time = cursor.fetchall()
            connection.close()
            
            # Transform data for the carousel format with only needed fields
            return [
                {
                    "id": student["StudentID"],
                    "name": f"{student['FirstName']} {student['LastName']}",
                    "percentage": f"{student['Percentage']}%"
                }
                for student in students_graduating_on_time
            ]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    

def get_students_without_prediction():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    s.StudentID,
                    s.FirstName,
                    s.LastName
                FROM students s
                LEFT JOIN prediction p ON s.StudentID = p.StudentID
                WHERE p.Prediction IS NULL OR p.Remarks = ''
            """)
            students_without_prediction = cursor.fetchall()
            connection.close()
            
            # Format data for carousel display
            return [
                {
                    "id": student["StudentID"],
                    "name": f"{student['FirstName']} {student['LastName']}",
                    "percentage": "N/A",
                    "factor": "",
                    "intervention": ""
                }
                for student in students_without_prediction
            ]
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        return None
    
# Function to fetch the count of events
def get_event_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM theevents")
            event_count = cursor.fetchone()['count']
            connection.close()
            return event_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        print("Failed to connect to the database.")
        return None

# Function to fetch the count of records in the academicintervention table
def get_academic_intervention_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM academicintervention")
            academic_count = cursor.fetchone()['count']
            connection.close()
            return academic_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        print("Failed to connect to the database.")
        return None

# Function to fetch the count of records in the behavioralintervention table
def get_behavioral_intervention_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM behavioralintervention")
            behavioral_count = cursor.fetchone()['count']
            connection.close()
            return behavioral_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        print("Failed to connect to the database.")
        return None

# Function to fetch the count of records in the socioeconomicintervention table
def get_socioeconomic_intervention_count():
    connection = connect_to_database()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM socioeconomicintervention")
            socioeconomic_count = cursor.fetchone()['count']
            connection.close()
            return socioeconomic_count
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            connection.close()
            return None
    else:
        print("Failed to connect to the database.")
        return None
    
def process_behavioral_data(df):
    # Define the scoring criteria
    scores = {
        'StudyHours': {
            'Less than 5 hours': 1, '5-10 hours': 2, '11-15 hours': 3, 
            '16-20 hours': 4, 'More than 20 hours': 5
        },
        'StudyStrategies': {
            'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5
        },
        'RegularStudySchedule': {'Yes': 5, 'No': 1},
        'AttendanceRate': {
            'Less than 50%': 1, '50-70%': 2, '71-90%': 3, 'More than 90%': 4
        },
        'ClassParticipation': {
            'Not at all': 1, 'Slightly': 2, 'Moderately': 3, 
            'Very actively': 4, 'Extremely actively': 5
        },
        'TimeManagementRating': {'Poor': 1, 'Fair': 2, 'Good': 3, 'Very Good': 4, 'Excellent': 5},
        'StudyDeadlinesFrequency': {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5},
        'MotivationLevel': {
            'Not motivated': 1, 'Slightly motivated': 2, 'Moderately motivated': 3, 
            'Very motivated': 4, 'Extremely motivated': 5
        },
        'EngagementLevel': {
            'Not engaged': 1, 'Slightly engaged': 2, 'Moderately engaged': 3, 
            'Very engaged': 4, 'Extremely engaged': 5
        },
        'StressFrequency': {'Never': 5, 'Rarely': 4, 'Sometimes': 3, 'Often': 2, 'Always': 1},
        'CopingEffectiveness': {
            'Not effective': 1, 'Slightly effective': 2, 'Moderately effective': 3, 
            'Very effective': 4, 'Extremely effective': 5
        },
    }

    # Connect to the database
    conn = connect_to_database()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        total_score = 0
        total_questions = 0

        # Calculate score for each field based on provided values
        for field, options in scores.items():
            if row[field] in options:
                total_score += options[row[field]]
                total_questions += 1

        # Calculate the average percentage
        average_percentage = (total_score / (total_questions * 5)) * 100 if total_questions > 0 else 0

        # Insert each row into the database
        cursor.execute("""
            INSERT INTO behavioral (
                StudentID, StudyHours, StudyStrategies, RegularStudySchedule,
                AttendanceRate, ClassParticipation, TimeManagementRating,
                StudyDeadlinesFrequency, MotivationLevel, EngagementLevel,
                StressFrequency, CopingEffectiveness, AveragePercentage
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['StudentID'], row['StudyHours'], row['StudyStrategies'],
            row['RegularStudySchedule'], row['AttendanceRate'], row['ClassParticipation'],
            row['TimeManagementRating'], row['StudyDeadlinesFrequency'],
            row['MotivationLevel'], row['EngagementLevel'], row['StressFrequency'],
            row['CopingEffectiveness'], average_percentage
        ))

    # Commit changes and close the database connection
    conn.commit()
    cursor.close()
    conn.close()

def process_grades_data(df):
    conn = connect_to_database()
    cursor = conn.cursor()

    # Disable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    for _, row in df.iterrows():
        try:
            # Insert data directly from the Excel file
            cursor.execute("""
                INSERT INTO grades (
                    StudentID, SubjectID, ProfessorID, MidtermGrade,
                    FinalGrade, SchoolYearID, SemesterID, ClassID, AverageGrade
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['StudentID'], row['SubjectID'], row['ProfessorID'],
                row['MidtermGrade'], row['FinalGrade'], row['SchoolYearID'],
                row['SemesterID'], row['ClassID'], row['AverageGrade']
            ))

        except Exception as e:
            print(f"Error inserting row: {row}\nException: {e}")

    # Enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()

