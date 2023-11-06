from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify  # Import jsonify
from pymongo import MongoClient
import bcrypt
import random
from bson import ObjectId  # Add this import statement for ObjectId
from datetime import datetime
import os 
from bson import ObjectId


app = Flask(__name__, static_url_path='/static')
app.secret_key = "12345" 

#static directory
static_dir = os.path.join(app.root_path, 'static')

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Aptitude"]

# admin Collection
admin_collection = db["admin"]

# Student Collection
student_collection = db["student"]

#created tests  collection
tests_collection = db["tests"] 

# Questions Collections
quants_collection = db["quants_questions"]
verbal_collection = db["verbal_questions"]
logical_collection = db["logical_questions"]

#uploaded test collection
uploaded_tests_collection= db["uploaded_tests"]

# This is the collection to store student test submissions
submission_collection = db['student_submissions']


@app.route('/')
def index():
    return render_template('index.html')

# admin Registration
@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check admin already exists
        if admin_collection.find_one({'email': email}):
            flash("Admin with this email already exists!", "danger")
        else:
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Initialize created_tests as an empty list for new admins
            admin_data = {'name': name, 'email': email, 'password': hashed_password, 'created_tests': [], 'uploaded_tests': [] }

            # Insert admin data into the collection
            admin_collection.insert_one(admin_data)
            flash("Admin registered successfully!", "success")
            return redirect('/admin_login')

    return render_template('admin_registration.html')


# admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user exists in admin collection
        admin = admin_collection.find_one({'email': email})
        if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password']):
            session['user_type'] = 'admin'
            session['user_email'] = email
            session['user_id'] = str(admin['_id'])  # Set the admin's ID in the session
            flash("Login successful!", "success")
            return redirect('/admin_dashboard')  # Replace with the admin dashboard route

        flash("Invalid admin credentials. Please try again.", "danger")

    return render_template('admin_login.html')


# Student Registration
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if student already exists
        if student_collection.find_one({'email': email}):
            flash("Student with this email already exists!", "danger")
        else:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # Insert student data into the collection
            # When registering a student initial score - 0
            student_collection.insert_one({'name': name, 'email': email, 'password': hashed_password})
            flash("Student registered successfully!", "success")
            return redirect('/student_login')  # Replace with the actual URL of your login page


    return render_template('student_registration.html')


# Student Login
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the user exists in student collection
        student = student_collection.find_one({'email': email})
        if student and bcrypt.checkpw(password.encode('utf-8'), student['password']):
            session['user_type'] = 'student'
            session['user_email'] = email
            session['user_name'] = student['name']  # Set the student's name in the session
            flash("Login successful!", "success")
            return redirect('/student_dashboard')  # Replace with the student dashboard route

        flash("Invalid student credentials. Please try again.", "danger")

    return render_template('student_login.html')


# Student Dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if 'user_type' in session and session['user_type'] == 'student':
        user_name = session['user_name']
        return render_template('student_dashboard.html', user_name=user_name)
    else:
        flash("You must be logged in as a student to access this page.", "warning")
        return redirect('/student_login')  # Redirect to student login if not logged in

@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'user_type' in session and session['user_type'] == 'admin':
        admin_email = session['user_email']

        # Fetch admin name from MongoDB
        admin = admin_collection.find_one({'email': admin_email})
        if admin:
            admin_name = admin['name']
            created_tests = admin.get('created_tests', [])
            uploaded_tests = admin.get('uploaded_tests', [])
        else:
            admin_name = "Name not found"
            created_tests = []
            uploaded_tests= []

        return render_template('admin_dashboard.html', user_email=admin_email, admin_name=admin_name, created_tests=created_tests, uploaded_tests=uploaded_tests)
    else:
        flash("You must be logged in as an admin to access the admin dashboard.", "warning")
        return redirect('/admin_login')


@app.route('/admin_profile')
def admin_profile():
    if 'user_type' in session and session['user_type'] == 'admin':
        admin_email = session['user_email']

        # Fetch admin details from the database
        admin_details = admin_collection.find_one({'email': admin_email}, {'name': 1, 'email': 1})

        if admin_details:
            return render_template('admin_profile.html', admin_details=admin_details)
        else:
            flash("Admin not found.", "danger")
            return redirect('/admin_dashboard')  # Redirect to admin dashboard if admin not found
    else:
        flash("You must be logged in as an admin to view your profile.", "warning")
        return redirect('/admin_login')

# Route for student profile page
@app.route('/student_profile', methods=['GET'])
def student_profile():
    if 'user_type' in session and session['user_type'] == 'student':
        student_email = session['user_email']

        # Fetch student details from MongoDB
        student = student_collection.find_one({'email': student_email})
        if student:
            student_name = student['name']
        else:
            student_name = "Name not found"  # Provide a default name or handle the case where the student is not found

        # Fetch test scores for the student from student_submissions collection
        scores = submission_collection.find({'student_email': student_email})

        return render_template('student_profile.html', student_name=student_name, student_email=student_email, scores=scores)
    else:
        flash("You must be logged in as a student to access the profile page.", "warning")
        return redirect('/student_login')


#teacher test part
@app.route('/create_test', methods=['GET', 'POST'])
def create_test():
    print("Entering create_test route")
    if 'user_type' in session and session['user_type'] == 'admin':
        if request.method == 'POST':
            print("Form Data:")
            print(f"Test Name: {request.form.get('test_name')}")
            print(f"Quants Questions: {request.form.get('quants_questions')}")
            print(f"Verbal Questions: {request.form.get('verbal_questions')}")
            print(f"Logical Questions: {request.form.get('logical_questions')}")

            admin_email = session['user_email']
            test_name = request.form.get('test_name')
            quants_count = int(request.form.get('quants_questions'))
            verbal_count = int(request.form.get('verbal_questions'))
            logical_count = int(request.form.get('logical_questions'))
            
            # Add code to retrieve the test duration entered by the teacher
            test_duration = int(request.form.get('test_duration'))

            # Fetch random questions from MongoDB for each section
            quants_questions = get_random_questions('quants', quants_count)
            verbal_questions = get_random_questions('verbal', verbal_count)
            logical_questions = get_random_questions('logical', logical_count)

            # Log the extracted values
            print(f"admin Email: {admin_email}")
            print(f"Test Name: {test_name}")
            print(f"Quants Count: {quants_count}")
            print(f"Verbal Count: {verbal_count}")
            print(f"Logical Count: {logical_count}")
            
            # Combine questions from all sections to create a test
            test_questions = quants_questions + verbal_questions + logical_questions

            # Check if test questions are empty
            if not test_questions:
                flash("No test questions available.", "danger")
                return redirect('/admin_dashboard')  # Redirect to admin dashboard if no questions

            # Store the test in the MongoDB collection with user details and test name
            test_data = {
                "admin_email": admin_email,
                "test_name": test_name,
                "test_questions": test_questions,
                "test_duration": test_duration,  # Add the test duration here
                "created_at": datetime.utcnow()
            }

            # Log the test_data dictionary for debugging
            print("Test Data:")
            for key, value in test_data.items():
                print(f"{key}: {value}")

            # Insert the test document into the 'tests' collection
            tests_collection = db['tests']
            test_id = tests_collection.insert_one(test_data).inserted_id

            # After creating the test, update the admin's record
            admin_email = session['user_email']  # Get the admin's email from the session
            test_name = request.form.get('test_name')  # Get the test name from the form

            # Assuming 'admin_collection' is your admin collection
            admin_collection.update_one(
                {'email': admin_email},
                {'$push': {'created_tests': test_name}}
            )


            # You can now use the 'test_id' to reference the saved test in the future.

            return render_template('display_test.html', test_questions=test_questions)

        return render_template('create_test.html')

    else:
        flash("You must be logged in as a admin to create a test.", "warning")
        return redirect('/admin_login')  # Redirect to admin login if not logged in


# Function to fetch random questions from MongoDB collections based on section
def get_random_questions(section, count):
    collection_names = {
        'quants': 'quants_questions',
        'verbal': 'verbal_questions',
        'logical': 'logical_questions'
    }

    if section in collection_names:
        collection_name = collection_names[section]
        collection = db[collection_name]

        random_questions = list(collection.aggregate([
            {'$sample': {'size': count}}
        ]))

        # Print the fetched questions for debugging
        print(f"Fetched {len(random_questions)} questions for {section} section")

        # Create a list to store the formatted question data
        formatted_questions = []

        for question in random_questions:
            # Create a dictionary for each question with the required fields
            formatted_question = {
                'question': question.get('Question', ''),
                'option1': question.get('Option 1', ''),
                'option2': question.get('Option 2', ''),
                'option3': question.get('Option 3', ''),
                'option4': question.get('Option 4', ''),
                'correct_answer': question.get('Correct Answer', '')
            }

            # Append the formatted question to the list
            formatted_questions.append(formatted_question)

        return formatted_questions  # Return the list of formatted question dictionaries

    return []


@app.route('/display_test', methods=['GET'])
def display_test():
    # Retrieve the test_questions from the session or your database
    test_questions = session.get('test_questions')

    if test_questions:
        return render_template('display_test.html', test_questions=test_questions)
    else:
        flash("No test questions available.", "danger")
        return redirect('/admin_dashboard')  #

@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_type' in session and session['user_type'] == 'admin':
        # Extract relevant data from the form
        test_id = request.form.get('test_id')  # Assuming you have a hidden field with the test ID in the form
        # Additional data extraction and validation as needed

        # Update the test record in the database with submission information
        # For example, you can set a 'submitted' flag and store the submission timestamp
        tests_collection.update_one(
            {'_id': ObjectId(test_id)},
            {'$set': {'submitted': True, 'submission_timestamp': datetime.utcnow()}}
        )
        print("Test submission logic executed successfully.")  # Add a print statement for debugging

        flash("Test submitted successfully!", "success")
        return redirect('/admin_dashboard')  # Redirect to the admin dashboard after submission

    else:
        flash("You must be logged in as an admin to submit a test.", "warning")
        return redirect('/admin_login')  # Redirect to the admin login page if not logged in

@app.route('/created_tests')
def created_tests():
    if 'user_type' in session and session['user_type'] == 'admin':
        admin_email = session['user_email']
        # Fetch admin name from MongoDB
        admin = admin_collection.find_one({'email': admin_email})
        if admin:
            admin_name = admin['name']
            created_tests = admin.get('created_tests', [])
        else:
            admin_name = "Name not found"
            created_tests = []
        print("admin-name = ",admin_email)

        # Fetch the list of tests created by the admin from the database
        created_tests = tests_collection.find({'admin_email': admin_email})

        return render_template('created_tests.html', created_tests=created_tests, admin_name=admin_name)
    else:
        flash("You must be logged in as an admin to view created tests.", "warning")
        return redirect('/admin_login')

@app.route('/view_test/<test_id>', methods=['GET'])
def view_test(test_id):
    try:
        # Convert the test_id from the URL to an ObjectId
        test_id = ObjectId(test_id)

        # Fetch the test details from MongoDB using the test_id
        test_details = tests_collection.find_one({'_id': test_id})

        if test_details:
            return render_template('view_test.html', test_details=test_details)
        else:
            flash("Test not found.", "danger")
            return redirect('/admin_dashboard')  # Redirect to admin dashboard if the test is not found

    except Exception as e:
        print(f"An error occurred while fetching the test details: {str(e)}")
        flash("An error occurred while fetching the test details.", "danger")
        return redirect('/admin_dashboard')  # Redirect to admin dashboard in case of an error




import pandas as pd
@app.route('/upload_test', methods=['GET', 'POST'])
def upload_test():
    if 'user_type' in session and session['user_type'] == 'admin':
        if request.method == 'POST':
            test_name = request.form.get('test_name')
            test_file = request.files['test_file']
            test_duration = int(request.form.get('test_duration', 0))  # Get the test duration

            if test_file:
                # Check if the uploaded file is an Excel or CSV file
                if test_file.filename.endswith(('.xlsx', '.xls', '.csv')):
                    try:
                        if test_file.filename.endswith(('.xlsx', '.xls')):
                            # Handle Excel file (xlsx or xls)
                            test_data = pd.read_excel(test_file)
                        elif test_file.filename.endswith('.csv'):
                            # Handle CSV file
                            test_data = pd.read_csv(test_file)

                        # Convert the test data to a JSON format or handle it as needed
                        # ...

                        # Save the test name, admin details, data, and test duration
                        uploaded_test_document = {
                            "admin_email": session['user_email'],
                            "test_name": test_name,
                            "test_data": test_data.to_dict(orient='records'),
                            "test_duration": test_duration,  # Store the test duration
                            "created_at": datetime.utcnow()
                        }
                        uploaded_test_id = uploaded_tests_collection.insert_one(uploaded_test_document).inserted_id
                        print("Uploaded Test Name:", test_name)

                        # After creating the test, update the admin's record
                        admin_email = session['user_email']
                        test_name = request.form.get('test_name')

                        admin_collection.update_one(
                            {'email': admin_email},
                            {'$push': {'uploaded_tests': test_name}}
                        )

                        flash("Test uploaded successfully!", "success")
                        return redirect('/admin_dashboard')

                    except Exception as e:
                        flash("Error processing the uploaded file.", "error")
                        print(e)

            flash("Invalid file format. Please upload an Excel (.xlsx) or CSV (.csv) file.", "error")

        return render_template('upload_test.html')

    else:
        flash("You must be logged in as an admin to upload a test.", "warning")
        return redirect('/admin_login')



#view uploaded tests
@app.route('/uploaded_tests')
def uploaded_tests():
    if 'user_type' in session and session['user_type'] == 'admin':
        admin_email = session['user_email']
        # Fetch admin name from MongoDB
        admin = admin_collection.find_one({'email': admin_email})
        if admin:
            admin_name = admin['name']
            uploaded_tests = admin.get('uploaded_tests', [])
        else:
            admin_name = "Name not found"
            created_tests = []
            uploaded_tets = []
        print("admin-name = ",admin_email)

        # Fetch the list of tests created by the admin from the database
        uploaded_tests = uploaded_tests_collection.find({'admin_email': admin_email})

        return render_template('uploaded_tests.html', uploaded_tests=uploaded_tests, admin_name=admin_name)
    else:
        flash("You must be logged in as an admin to view created tests.", "warning")
        return redirect('/admin_login')


@app.route('/view_uploaded_test/<test_id>', methods=['GET'])
def view_uploaded_test(test_id):
    try:
        # Convert the test_id from the URL to an ObjectId
        test_id = ObjectId(test_id)

        # Fetch the uploaded test details from MongoDB using the test_id
        uploaded_test_details = uploaded_tests_collection.find_one({'_id': test_id})

        if uploaded_test_details:
            # Extract the list of test questions from the uploaded test data
            test_data = uploaded_test_details.get('test_data', [])

            # Pass 'uploaded_test_details' and 'test_data' to the template for rendering
            return render_template('view_uploaded_test.html', uploaded_test_details=uploaded_test_details, test_data=test_data)
        else:
            flash("Test not found.", "danger")
            return redirect('/admin_dashboard')  # Redirect to admin dashboard if the test is not found

    except Exception as e:
        print(f"An error occurred while fetching the uploaded test details: {str(e)}")
        flash("An error occurred while fetching the uploaded test details.", "danger")
        return redirect('/admin_dashboard')  # Redirect to admin dashboard in case of an error

#student section

@app.route('/available_tests')
def available_tests():
    if 'user_type' in session and session['user_type'] == 'student':
        student_email = session['user_email']

        # Fetch the list of tests created and uploaded by admins
        created_tests = tests_collection.find({'admin_email': {'$exists': True}})
        uploaded_tests = uploaded_tests_collection.find({})

        # Check if the student has already submitted each test
        available_created_tests = []
        available_uploaded_tests = []

        for test in created_tests:
            test_id = test['_id']
            # Check if there is a submission by this student for the test
            existing_submission = submission_collection.find_one({
                'student_email': student_email,
                'test_id': test_id
            })

            if not existing_submission:
                available_created_tests.append(test)

        for test in uploaded_tests:
            test_id = test['_id']
            # Check if there is a submission by this student for the test
            existing_submission = submission_collection.find_one({
                'student_email': student_email,
                'test_id': test_id
            })

            if not existing_submission:
                available_uploaded_tests.append(test)

        return render_template('available_tests.html', available_created_tests=available_created_tests, available_uploaded_tests=available_uploaded_tests)
    else:
        flash("You must be logged in as a student to view available tests.", "warning")
        return redirect('/student_login')

#attempt test
# Modify the 'attempt_test' route
@app.route('/attempt_test/<test_type>/<test_id>', methods=['GET'])
def attempt_test(test_type, test_id):
    try:
        # Convert the test_id from the URL to an ObjectId
        test_id = ObjectId(test_id)

        # Fetch the test details from the appropriate collection based on 'test_type'
        if test_type == 'created':
            test_details = tests_collection.find_one({'_id': test_id})
            if test_details:
                timer_duration = test_details.get('test_duration', 0)  # Fetch the timer duration from the test details
                test_name = test_details.get('test_name', 'Test')
        else:
            flash("Invalid test type.", "danger")
            return redirect('/available_tests')  # Redirect to available tests page

        if timer_duration > 0:  # Check if the timer is set
            timer_duration_minutes = timer_duration
        else:
            timer_duration_minutes = 0

        if test_details:
            # Render the 'attempt_test.html' template with the test details, test data, and timer information
            return render_template(
                'attempt_test.html',
                test_details=test_details,
                test_data=test_details['test_questions'],
                timer_duration=timer_duration_minutes,
                test_name=test_name
            )
        else:
            flash("Test not found.", "danger")
            return redirect('/available_tests')  # Redirect to available tests page if the test is not found

    except Exception as e:
        print(f"An error occurred while fetching the test details: {str(e)}")
        flash("An error occurred while fetching the test details.", "danger")
        return redirect('/available_tests')  # Redirect to available tests page in case of an error


from datetime import datetime, timedelta

from datetime import datetime

def is_time_up(timer_end_time):
    current_time = datetime.now()
    return current_time >= timer_end_time


def get_timer_end_time(test_duration):
    # Convert test_duration from minutes to seconds
    test_duration_seconds = test_duration * 60

    # Calculate the end time of the timer
    current_time = datetime.now()
    timer_end_time = current_time + timedelta(seconds=test_duration_seconds)

    return timer_end_time

# Now you can use this function in your Flask route or view

from datetime import datetime, timedelta


# Add the timer-related functions

def is_time_up(timer_end_time):
    current_time = datetime.now()
    return current_time >= timer_end_time


def get_timer_end_time(test_duration):
    # Convert test_duration from minutes to seconds
    test_duration_seconds = test_duration * 60

    # Calculate the end time of the timer
    current_time = datetime.now()
    timer_end_time = current_time + timedelta(seconds=test_duration_seconds)
    return timer_end_time


# Update the 'attempt_uploaded_test' route

@app.route('/attempt_uploaded_test/<test_type>/<test_id>', methods=['GET'])
def attempt_uploaded_test(test_type, test_id):
    print("Reached the attempt_uploaded_test route")  # Debugging output
    try:
        # Convert the test_id from the URL to an ObjectId
        test_id = ObjectId(test_id)

        # Fetch the test details from the uploaded_tests_collection using the provided test_id
        if test_type == 'uploaded':
            test_details = uploaded_tests_collection.find_one({'_id': test_id})

        else:
            flash("Invalid test type.", "danger")
            return redirect('/available_tests')

        if test_details:
            if 'test_data' in test_details:
                test_data = test_details.get('test_data', [])

            timer_duration = test_details.get('test_duration', 0)
            timer_end_time = get_timer_end_time(timer_duration)  # Calculate the timer end time

            if is_time_up(timer_end_time):
                # Automatic test submission if time is up
                flash("Test submitted automatically. Time is up.", "success")
                return redirect('/student_dashboard')  # Redirect to student dashboard after submission

            # Render the 'attempt_uploaded_test.html' template with the test details and timer information
            return render_template('attempt_uploaded_test.html', test_details=test_details, test_type=test_type,
                                   test_data=test_data, timer_duration=timer_duration, timer_end_time=timer_end_time)
        else:
            flash("Test not found.", "danger")
            return redirect('/available_tests')  # Redirect to available tests page if the test is not found

    except Exception as e:
        print(f"An error occurred while fetching the test details: {str(e)}")
        flash("An error occurred while fetching the test details.", "danger")
        return redirect('/available_tests')  # Redirect to available tests page in case of an error


@app.route('/submit_uploaded_test/<test_id>', methods=['POST'])
def submit_uploaded_test(test_id):
    try:
        # Fetch the test details from MongoDB using the test_id
        test_id = ObjectId(test_id)
        test_details = uploaded_tests_collection.find_one({'_id': test_id})

        if test_details:
            # Determine the source of the test data (form or uploaded file)
            test_data_field = 'test_data'  # Update this based on your data structure

            if test_data_field in test_details:
                # The test was uploaded via a file
                test_data = test_details.get(test_data_field, [])

                # Handle student's test submission here and calculate the score
                # You can compare the submitted answers with the correct answers

                student_answers = {}
                score = 0

                for i, question_data in enumerate(test_data):
                    question_id = str(i + 1)
                    selected_answer = request.form.get(f'question_{question_id}')
                    correct_answer = question_data['Correct Answer']

                    print(f"Question {question_id}:")
                    print(f"Submitted Answer: {selected_answer}")
                    print(f"Correct Answer: {correct_answer}")

                    if selected_answer == correct_answer:
                        score += 2

                    student_answers[question_id] = {
                        'question': question_data['Question'],
                        'submitted_answer': selected_answer,
                        'correct_answer': correct_answer
                    }

                # Calculate the score based on the student's responses
                total_questions = len(test_data)
                percentage_score = (score / total_questions) * 100

                # Store student details and test name in the submission collection
                student_email = session.get('user_email')
                student_name = session.get('user_name')
                submission_record = {
                    'student_email': student_email,
                    'student_name': student_name,
                    'test_id': test_id,
                    'test_name': test_details['test_name'],
                    'score': percentage_score,
                    'submission_time': datetime.utcnow()
                }
                submission_collection.insert_one(submission_record)

                flash("Test submitted successfully!", "success")

                # Debug statement to check if the test was submitted successfully
                print(f"Test submitted by {student_name} ({student_email}) for test '{test_details['test_name']}' with a score of {percentage_score}%")

                return redirect('/student_dashboard')  # Redirect to student dashboard after submission

            else:
                flash("Test data not found.", "danger")
                return redirect('/student_dashboard')

        else:
            flash("Test not found.", "danger")
            return redirect('/student_dashboard')

    except Exception as e:
        print(f"An error occurred while processing the test submission: {str(e)}")
        flash("An error occurred while processing the test submission.", "danger")
        return redirect('/student_dashboard')  # Redirect to student dashboard in case of an error


@app.route('/submit_created_test/<test_id>', methods=['POST'])
def submit_created_test(test_id):
    try:
        # Fetch the test details from MongoDB using the test_id
        test_id = ObjectId(test_id)
        test_details = tests_collection.find_one({'_id': test_id})

        if test_details:
            # Determine the source of the test data (form or uploaded file)
            test_data_field = 'test_questions'  # Update this based on your data structure

            if test_data_field in test_details:
                # The test was created through a form
                test_data = test_details.get(test_data_field, [])

                # Check if the time is up by calling the is_time_up function
                timer_duration = test_details.get('test_duration', 0)
                timer_end_time = get_timer_end_time(timer_duration)
                if is_time_up(timer_end_time):
                    # Automatic test submission if time is up
                    flash("Test submitted automatically. Time is up.", "success")

                    # You can update the submission record with a special flag to indicate automatic submission
                    # For example, add a key-value pair like 'submitted_auto': True
                    # Modify the submission record accordingly

                    return redirect('/student_dashboard')  # Redirect to student dashboard after submission

                # Continue with manual submission if time is not up
                student_answers = {}
                score = 0

                for i, question_data in enumerate(test_data):
                    question_id = str(i + 1)
                    selected_answer = request.form.get(f'question_{question_id}')
                    correct_answer = question_data['correct_answer']

                    print(f"Question {question_id}:")
                    print(f"Submitted Answer: {selected_answer}")
                    print(f"Correct Answer: {correct_answer}")

                    if selected_answer == correct_answer:
                        score += 2

                    student_answers[question_id] = {
                        'question': question_data['question'],
                        'submitted_answer': selected_answer,
                        'correct_answer': correct_answer
                    }

                # Calculate the score based on the student's responses
                total_questions = len(test_data)
                percentage_score = (score / total_questions) * 100

                # Store student details and test name in the submission collection
                student_email = session.get('user_email')
                student_name = session.get('user_name')
                submission_record = {
                    'student_email': student_email,
                    'student_name': student_name,
                    'test_id': test_id,
                    'test_name': test_details['test_name'],
                    'score': percentage_score,
                    'submission_time': datetime.utcnow()
                }
                submission_collection.insert_one(submission_record)

                flash("Test submitted successfully!", "success")

                # Debug statement to check if the test was submitted successfully
                print(f"Test submitted by {student_name} ({student_email}) for test '{test_details['test_name']}' with a score of {percentage_score}%")

                return redirect('/student_dashboard')  # Redirect to student dashboard after submission

            else:
                flash("Test data not found.", "danger")
                return redirect('/student_dashboard')

        else:
            flash("Test not found.", "danger")
            return redirect('/student_dashboard')

    except Exception as e:
        print(f"An error occurred while processing the test submission: {str(e)}")
        flash("An error occurred while processing the test submission.", "danger")
        return redirect('/student_dashboard')  # Redirect to student dashboard in case of an error


"""@app.route('/see_student_scores/<admin_email>', methods=['GET'])
def see_student_scores(admin_email):
    try:
        # Fetch the admin's name from MongoDB
        admin = admin_collection.find_one({'email': admin_email})
        if admin:
            admin_name = admin['name']
        else:
            admin_name = "Admin Name Not Found"  # Provide a default name or handle the case where the admin is not found

        # Fetch test IDs created or uploaded by the admin
        admin_tests = tests_collection.find({'admin_email': admin_email}, {'_id': 1})
        admin_test_ids = [test['_id'] for test in admin_tests]

        # Fetch student scores for the admin's tests
        scores = submission_collection.find({
            'student_email': admin_email,
            'test_id': {'$in': admin_test_ids}
        })

        return render_template('see_student_scores.html', admin_name=admin_name, scores=scores, admin_email=admin_email)
    except Exception as e:
        # Handle exceptions and errors here...
        flash("An error occurred while fetching student scores.", "danger")
        return redirect('/admin_dashboard')  # Redirect to admin dashboard in case of an error

"""
@app.route('/see_student_scores/<admin_email>', methods=['GET'])
def see_student_scores(admin_email):
    try:
        # Fetch the admin's name from MongoDB
        admin = admin_collection.find_one({'email': admin_email})
        if admin:
            admin_name = admin['name']
        else:
            admin_name = "Admin Name Not Found"  # Provide a default name or handle the case where the admin is not found

        # Fetch test names created by the admin
        admin_created_tests = admin.get('created_tests', [])
        admin_uploaded_tests = admin.get('uploaded_tests', [])
        admin_test_names = admin_created_tests + admin_uploaded_tests

        # Fetch student scores for the admin's tests based on test_name
        student_scores = submission_collection.find({
            'test_name': {'$in': admin_test_names}
        })

        return render_template('see_student_scores.html', admin_name=admin_name, student_scores=student_scores, admin_email=admin_email)
    except Exception as e:
        # Handle exceptions and errors here...
        flash("An error occurred while fetching student scores.", "danger")
        return redirect('/admin_dashboard')  # Redirect to admin dashboard in case of an error


import subprocess





@app.route('/scrapy')
def scrap_real_time_questions():
    try:
        # Execute the scrap.py script
        subprocess.run(['python', 'scrap.py'])
        # If the script execution is successful, you can redirect the user or show a message
        return "Scraping completed successfully!"
    except Exception as e:
        # Handle any exceptions that may occur during scraping
        return f"An error occurred: {str(e)}"



if __name__ == '__main__':
    app.run(debug=True)

