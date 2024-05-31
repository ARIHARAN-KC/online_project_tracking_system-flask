#import statements
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from flask import Flask, jsonify,render_template, redirect, request, url_for, flash, session
from flask_mysqldb import MySQL
from MySQLdb import IntegrityError
import MySQLdb.cursors
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from forms import AddTaskForm, ChangePasswordForm, LoginForm, ProjectAssignForm, ProjectTasksForm, RegisterForm, GuideRegistrationForm, ProjectForm, StudentRegistrationForm,CommentForm,StatusUpdateForm, TaskStatusForm,  UploadForm
from flask_wtf.csrf import CSRFProtect  
import random
import string
from datetime import datetime
from dateutil.relativedelta import relativedelta
#----------------------------------------------------------------------#
#secrect key generation (encryption)
def generate_secret_key(length=24):
    characters = string.ascii_letters + string.digits + string.punctuation
    secret_key = ''.join(random.choice(characters) for _ in range(length))
    return secret_key

secret_key = generate_secret_key()

app = Flask(__name__)
app.secret_key = secret_key
csrf = CSRFProtect(app)  # Initialize CSRF protection with your Flask app instance
#------------------------------------------------------------------------#
#database connections
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Root_100'
app.config['MYSQL_DB'] = 'project_management'

mysql = MySQL(app)
#------------------------------------------------------------------------#
# Define UserMixin class for user authentication
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)
#-------------------------------------------------------------------------#
#base and dashboard routes
@app.route('/')
def home():
    return render_template('base.html')

@app.route('/index')
def index():
    return render_template('index.html')

def calculate_completed_projects():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM assign_projects WHERE status = 'completed'")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        flash('An error occurred while calculating completed projects: {}'.format(str(e)), 'error')
        return 0

def calculate_in_process_projects():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM assign_projects WHERE status = 'in progress'")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        flash('An error occurred while calculating in-process projects: {}'.format(str(e)), 'error')
        return 0

def calculate_stuck_projects():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM assign_projects WHERE status = 'stuck'")
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        flash('An error occurred while calculating stuck projects: {}'.format(str(e)), 'error')
        return 0

# Route for dashboard
@app.route('/dashboard')
def dashboard():
    # Assuming you have logic to calculate the number of completed, in-process, and stuck projects
    completed_projects = calculate_completed_projects()
    in_process_projects = calculate_in_process_projects()
    stuck_projects = calculate_stuck_projects()
    
    return render_template('dashboard.html', completed_projects=completed_projects, 
                           in_process_projects=in_process_projects, stuck_projects=stuck_projects)


# Guide Dashboard route
@app.route('/guide/dashboard')
def guide_dashboard():
    if 'id' in session and session.get('role') == 'guide':
        try:
            guide_id = session['id']
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                SELECT project_id  
                FROM assign_projects 
                WHERE guide_id = %s 
            ''', (guide_id,))
            
            project_id = cursor.fetchone()
            cursor.close()

            if project_id:
                return render_template('guide/dashboard.html', project_id=project_id[0])
            else:
                flash('No project assigned to you.', 'warning')
                return render_template('guide/dashboard.html')
        
        except Exception as e:
            flash('An error occurred while fetching the project details: {}'.format(str(e)), 'error')
            return redirect(url_for('guide_login'))
    else:
        flash('Please login as a guide to access the dashboard.', 'error')
        return redirect(url_for('guide_login'))
    
# Student Dashboard route
@app.route('/student/dashboard')
def student_dashboard():
    if 'id' in session and session.get('role') == 'student':
        try:
            student_id = session['id']
            
            cursor = mysql.connection.cursor()
            cursor.execute('''
                SELECT project_id 
                FROM assign_projects 
                WHERE team_leader_id = %s
                OR student1_id = %s 
                OR student2_id = %s 
                OR student3_id = %s 
                OR student4_id = %s
            ''', (student_id,student_id, student_id, student_id, student_id))
            project_id = cursor.fetchone()
            cursor.close()

            if project_id:
                return render_template('student/dashboard.html', project_id=project_id[0])
            else:
                flash('No project assigned to you.', 'warning')
                return render_template('student/dashboard.html')
        
        except Exception as e:
            flash('An error occurred while fetching the project details: {}'.format(str(e)), 'error')
            return redirect(url_for('student_login'))
    else:
        flash('Please login as a student to access the dashboard.', 'error')
        return redirect(url_for('student_login'))

#------------------------------------------------------------------------------------------------------#
# Admin routes
# admin register route
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('INSERT INTO admin (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
            mysql.connection.commit()
            flash('Admin registered successfully.', 'success')
            return redirect(url_for('admin_login'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Failed to register admin. Error: {}'.format(str(e)), 'error')
        finally:
            cursor.close()
    return render_template('admin/register.html', form=form)

# admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin WHERE username = %s', (username,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin['password'], password):
            session['loggedin'] = True
            session['id'] = admin['id']
            session['username'] = admin['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect username or password!', 'error')
    return render_template('admin/login.html', form=form)

# admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# admin register guide route
@app.route('/admin/register-guide', methods=['GET', 'POST'])
def admin_register_guide():
    form = GuideRegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        guide_id = form.id.data  
        guide_name = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('INSERT INTO guides (id, username, email, password) VALUES (%s, %s, %s, %s)', (guide_id, guide_name, email, password))
            mysql.connection.commit()
            flash('Guide registered successfully.', 'success')
            return redirect(url_for('admin_view_guides'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Failed to register guide. Error: {}'.format(str(e)), 'error')
        finally:
            cursor.close()
    return render_template('admin/register_guide.html', form=form)

# admin view-guides routes
@app.route('/admin/view-guides')
def admin_view_guides():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('SELECT * FROM guides')
        guides = cursor.fetchall()
        cursor.close()
        form = GuideRegistrationForm() 
        return render_template('admin/view_guides.html', guides=guides, form=form)
    except Exception as e:
        flash('Failed to fetch guides. Error: {}'.format(str(e)), 'error')
        cursor.close()
        return redirect(url_for('admin_login'))

# admin remove-guide routes
@app.route('/admin/remove-guide/<string:guide_id>', methods=['POST'])
def admin_remove_guide(guide_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('SELECT * FROM assign_projects WHERE guide_id = %s', (guide_id,))
        related_projects = cursor.fetchall()
        if related_projects:
            flash('Cannot remove guide. There are related projects assigned to this guide.', 'error')
            return redirect(url_for('admin_view_guides'))
        else:
            cursor.execute('DELETE FROM guides WHERE id = %s', (guide_id,))
            mysql.connection.commit()
            flash('Guide removed successfully.', 'success')
            return redirect(url_for('admin_view_guides'))
    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to remove guide. Error: {}'.format(str(e)), 'error')
        cursor.close()
        return redirect(url_for('admin_view_guides'))

# admin register student route
@app.route('/admin/register-student', methods=['GET', 'POST'])
def admin_register_student():
    form = StudentRegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        student_id = form.id.data  
        student_name = form.username.data
        email = form.email.data
        password = generate_password_hash(form.password.data)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('INSERT INTO students (id, username, email, password) VALUES (%s, %s, %s, %s)', (student_id, student_name, email, password))
            mysql.connection.commit()
            flash('Student registered successfully.', 'success')
            return redirect(url_for('admin_view_students'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Failed to register student. Error: {}'.format(str(e)), 'error')
        finally:
            cursor.close()
    return render_template('admin/register_students.html', form=form)

# admin view-students routes
@app.route('/admin/view-students')
def admin_view_students():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('SELECT * FROM students')
        students = cursor.fetchall()
        cursor.close()
        form = StudentRegistrationForm() 
        return render_template('admin/view_students.html', students=students, form=form)
    except Exception as e:
        flash('Failed to fetch students. Error: {}'.format(str(e)), 'error')
        cursor.close()
        return redirect(url_for('admin_login'))

# admin remove-student routes
@app.route('/admin/remove-student/<string:student_id>', methods=['POST'])
def admin_remove_student(student_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('DELETE FROM students WHERE id = %s', (student_id,))
        mysql.connection.commit()
        flash('Student removed successfully.', 'success')
        return redirect(url_for('admin_view_students'))
    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to remove student. Error: {}'.format(str(e)), 'error')
        cursor.close()
        return redirect(url_for('admin_view_students'))

#admin add project route
@app.route('/admin/add-project', methods=['GET', 'POST'])
def admin_add_project():
    form = ProjectForm()  
    if request.method == 'POST' and form.validate_on_submit():
        project_name = form.name.data
        description = form.description.data
        start_date = request.form['start_date'] 

      
        end_date = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1) + relativedelta(months=1)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO projects (name, description, start_date, end_date) VALUES (%s, %s, %s, %s)', (project_name, description, start_date, end_date))
        
        mysql.connection.commit()
        cursor.close()
        flash('Project added successfully.', 'success')
        return redirect(url_for('admin_view_projects'))
    return render_template('admin/add_project.html', form=form)

# admin route for edit project description
@app.route('/admin/edit-project-description/<int:project_id>', methods=['POST'])
def admin_edit_project_description(project_id):
    if request.method == 'POST':
        new_description = request.form['description']

        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE projects SET description = %s WHERE id = %s', (new_description, project_id))
        mysql.connection.commit()
        cursor.close()

        flash('Project description updated successfully.', 'success')
        return redirect(url_for('admin_view_projects'))

    return redirect(url_for('admin_view_projects'))

@app.route('/admin/view-projects', methods=['GET', 'POST'])
def admin_view_projects():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    search = request.args.get('search')
    if search:
        cursor.execute('''
            SELECT projects.*, assign_projects.status, guides.username AS assigned_guide_name 
            FROM projects 
            LEFT JOIN assign_projects ON projects.id = assign_projects.project_id 
            LEFT JOIN guides ON assign_projects.guide_id = guides.id
            WHERE projects.name LIKE %s
        ''', ('%' + search + '%',))
    else:
        cursor.execute('''
            SELECT projects.*, assign_projects.status, guides.username AS assigned_guide_name 
            FROM projects 
            LEFT JOIN assign_projects ON projects.id = assign_projects.project_id 
            LEFT JOIN guides ON assign_projects.guide_id = guides.id
        ''')
    projects = cursor.fetchall()
    cursor.close()
    form = ProjectForm()  
    return render_template('admin/view_projects.html', projects=projects, form=form)

#admin assign project route
@app.route('/admin/assign-project', methods=['GET', 'POST'])
def admin_assign_project():
    form = ProjectAssignForm()

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT id, name FROM projects')
    projects = cursor.fetchall()
    cursor.execute('SELECT id, username FROM guides')
    guides = cursor.fetchall()
    cursor.execute('SELECT id, username FROM students')
    students = cursor.fetchall()
    cursor.close()

    form.project_id.choices = [(project['id'], project['name']) for project in projects]
    form.guide_id.choices = [(str(guide['id']), guide['username']) for guide in guides]
    form.team_leader_id.choices = [(str(student['id']), student['username']) for student in students]
    form.student1_id.choices = [(str(student['id']), student['username']) for student in students]
    form.student2_id.choices = [(str(student['id']), student['username']) for student in students]
    form.student3_id.choices = [(str(student['id']), student['username']) for student in students]
    form.student4_id.choices = [(str(student['id']), student['username']) for student in students]

    if request.method == 'POST' and form.validate_on_submit():
       
        project_id = form.project_id.data
        guide_id = form.guide_id.data
        team_leader_id = form.team_leader_id.data
        student1_id = form.student1_id.data
        student2_id = form.student2_id.data
        student3_id = form.student3_id.data
        student4_id = form.student4_id.data
        start_date = form.start_date.data
        end_date = form.end_date.data

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO assign_projects (project_id, guide_id, team_leader_id, student1_id, student2_id, student3_id, student4_id, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (project_id, guide_id, team_leader_id, student1_id, student2_id, student3_id, student4_id, start_date, end_date))
            mysql.connection.commit()
            flash('Project assigned successfully', 'success')
            return redirect(url_for('admin_view_projects'))
        except Exception as e:
            mysql.connection.rollback()
            flash('Failed to assign project. Error: {}'.format(str(e)), 'error')
        finally:
            cursor.close()

    return render_template('admin/assign_project.html', form=form, projects=projects, guides=guides, students=students)

@app.route('/admin/remove-project/<int:project_id>', methods=['POST'])
def admin_remove_project(project_id):
    cursor = mysql.connection.cursor()
    try:
        # Start a transaction
        cursor.execute('START TRANSACTION')

        cursor.execute('DELETE FROM assign_projects WHERE project_id = %s', (project_id,))
        cursor.execute('DELETE FROM comment WHERE project_id = %s', (project_id,))
        cursor.execute('DELETE FROM tasks WHERE project_id = %s', (project_id,))
        cursor.execute('DELETE FROM projects WHERE id = %s', (project_id,))

        mysql.connection.commit()
        flash('Project and related data removed successfully.', 'success')

    except Exception as e:
        mysql.connection.rollback()
        flash('Failed to remove project. Error: {}'.format(str(e)), 'error')
    finally:
        cursor.close()

    return redirect(url_for('admin_view_projects'))

# Assuming you have already defined the necessary imports and setup

@app.route('/admin/upload-guide-csv', methods=['GET', 'POST'])
def upload_guide_csv():
    form = UploadForm()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            csv_data = file.read().decode('utf-8').splitlines()

            cursor = mysql.connection.cursor()
            guides_added = []
            guides_failed = []

            for line in csv_data:
                data = line.split(',')
                if len(data) == 4:
                    try:
                        cursor.execute('INSERT INTO guides (id, username, email, password) VALUES (%s, %s, %s, %s)', (data[0], data[1], data[2], generate_password_hash(data[3])))
                        guides_added.append(data[0])
                    except IntegrityError as e:
                        error_code = e.args[0]
                        if error_code == 1062:  # Duplicate entry error code
                            guides_failed.append(data[0])
                        else:
                            flash(f'Error occurred while uploading guide with ID {data[0]}', 'error')
                else:
                    flash('Invalid format in CSV file', 'error')
                    return redirect(request.url)

            mysql.connection.commit()
            cursor.close()

            if guides_added:
                flash(f'Guides {", ".join(guides_added)} uploaded successfully', 'success')
            if guides_failed:
                flash(f'Guides {", ".join(guides_failed)} already exist ', 'error')

            return redirect(url_for('upload_guide_csv'))

        flash('Invalid file format. Please upload a CSV file.', 'error')

    return render_template('admin/upload_guide_csv.html', form=form)

@app.route('/admin/view-project-tasks/<int:project_id>', methods=['GET', 'POST'])
def view_project_tasks(project_id):
    form = ProjectTasksForm()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tasks WHERE project_id = %s', (project_id,))
    tasks = cursor.fetchall()
    cursor.close()
    return render_template('admin/view_project_tasks.html', tasks=tasks, form=form)


# Assuming you have already defined the necessary imports and setup

@app.route('/admin/upload-student-csv', methods=['GET', 'POST'])
def upload_student_csv():
    form = UploadForm()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            csv_data = file.read().decode('utf-8').splitlines()

            cursor = mysql.connection.cursor()
            students_added = []
            students_failed = []

            for line in csv_data:
                data = line.split(',')
                if len(data) == 4:
                    try:
                        cursor.execute('INSERT INTO students (id, username, email, password) VALUES (%s, %s, %s, %s)', (data[0], data[1], data[2], generate_password_hash(data[3])))
                        students_added.append(data[0])
                    except IntegrityError as e:
                        error_code = e.args[0]
                        if error_code == 1062:  # Duplicate entry error code
                            students_failed.append(data[0])
                        else:
                            flash(f'Error occurred while uploading student with ID {data[0]}', 'error')
                else:
                    flash('Invalid format in CSV file', 'error')
                    return redirect(request.url)

            mysql.connection.commit()
            cursor.close()

            if students_added:
                flash(f'Students {", ".join(students_added)} uploaded successfully', 'success')
            if students_failed:
                flash(f'Students {", ".join(students_failed)} already exist ', 'error')

            return redirect(url_for('upload_student_csv'))

        flash('Invalid file format. Please upload a CSV file.', 'error')

    return render_template('admin/upload_student_csv.html', form=form)

# Gantt Charts Routes
@app.route('/admin/projects/<int:project_id>/gantt-chart')
def project_gantt_chart(project_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tasks WHERE project_id = %s", (project_id,))
    tasks = cursor.fetchall()
    cursor.close()

    gantt_chart_data = []
    for task in tasks:
        gantt_chart_data.append({
            'Task': task['name'],
            'Start': task['start_date'].strftime('%Y-%m-%d'),  # Format date properly
            'End': task['end_date'].strftime('%Y-%m-%d')  # Format date properly
        })

    return render_template('gantt_chart.html', gantt_chart_data=gantt_chart_data)

# Route to generate and display project completion report
@app.route('/admin/generate-project-report')
def generate_project_report():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Fetch data needed for the report from the database
        cursor.execute('SELECT id, name, start_date, end_date FROM projects')
        projects = cursor.fetchall()
        
        # Calculate completion percentage for each project
        for project in projects:
            cursor.execute("SELECT COUNT(*) as total_tasks FROM tasks WHERE project_id = %s", (project['id'],))
            total_tasks = cursor.fetchone()['total_tasks']
            cursor.execute("SELECT COUNT(*) as completed_tasks FROM tasks WHERE project_id = %s AND task_status = 'Completed'", (project['id'],))
            completed_tasks = cursor.fetchone()['completed_tasks']
            
            if total_tasks > 0:
                project['completion_percentage'] = (completed_tasks / total_tasks) * 100
            else:
                project['completion_percentage'] = 0
        
        # Plotting the completion percentage
        plt.figure(figsize=(10, 6))
        project_names = [project['name'] for project in projects]
        completion_percentages = [project['completion_percentage'] for project in projects]
        plt.barh(project_names, completion_percentages, color='skyblue')
        plt.xlabel('Completion Percentage')
        plt.ylabel('Project Name')
        plt.title('Project Completion Report')
        plt.gca().invert_yaxis()  # Invert y-axis to display projects from top to bottom
        plt.xlim(0, 100)  # Limit x-axis from 0 to 100
        plt.grid(axis='x')  # Add grid lines along x-axis
        plt.tight_layout()

        # Save plot as bytes
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return render_template('admin/project_report.html', projects=projects, plot=f'<img src="data:image/png;base64,{plot_url}" />')
    
    except Exception as e:
        flash('Failed to generate project report. Error: {}'.format(str(e)), 'error')
        return redirect(url_for('admin_login'))
    finally:
        cursor.close()
#-----------------------------------------------------------------------------------------------------------#
# Guide routes

#guide route for login
@app.route('/guide/login', methods=['GET', 'POST'])
def guide_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM guides WHERE username = %s', (username,))
        guide = cursor.fetchone()
        cursor.close()

        if guide and check_password_hash(guide['password'], password):
            session['id'] = guide['id']  # Set the 'id' key in the session
            session['username'] = guide['username']
            session['role'] = 'guide'
            flash('Logged in successfully!', 'success')
            return redirect(url_for('guide_dashboard'))
        else:
            flash('Incorrect username or password!', 'error')

    return render_template('guide/login.html', form=form)

#guide logout route
@app.route('/guide/logout')
def guide_logout():
    session.pop('role', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# guide route for display assigned projects
@app.route('/guide/projects')
def guide_projects():
    if 'username' in session:  
        guide_username = session['username']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id FROM guides WHERE username = %s', (guide_username,))
        guide_id = cursor.fetchone()
        cursor.close()

        if guide_id:  
            guide_id = guide_id[0]
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('''
            SELECT assign_projects.*, projects.name AS project_name
            FROM assign_projects
            JOIN projects ON assign_projects.project_id = projects.id
            WHERE assign_projects.guide_id = %s
        ''', (str(guide_id),))

            assigned_projects = cursor.fetchall()
            cursor.close()

            # Fetch project_id
            project_id = assigned_projects[0]['project_id']

            return render_template('guide/projects.html', assigned_projects=assigned_projects, project_id=project_id)
        else:
            flash('Guide not found!', 'error')
            return redirect(url_for('guide_login'))  
    else:
        return redirect(url_for('guide_login'))

#guide routes for add comments
@app.route('/add_comment/<int:project_id>', methods=['GET', 'POST'])
def add_comment(project_id):
    form = CommentForm()
    if form.validate_on_submit():
        display_name = form.display_name.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        
        cursor.execute(
            "INSERT INTO comment (displayName, content, project_id) VALUES (%s, %s, %s)",
            (display_name, content, project_id)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Comment added successfully!', 'success')
        return redirect(url_for('project_details', project_id=project_id))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.execute("SELECT * FROM comment WHERE project_id = %s", (project_id,))
    comments = cursor.fetchall()
    cursor.close()
    
    return render_template('guide/add_comment.html', title='Add Comment', form=form, project=project, comments=comments)

#guide routes for display comments
@app.route('/project_details/<int:project_id>')
def project_details(project_id):
   
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()


    cursor.execute("SELECT * FROM comment WHERE project_id = %s", (project_id,))
    comments = cursor.fetchall()
    cursor.close()
    # Close the cursor (not the database connection)
    cursor.close()
    return render_template('guide/project_details.html', project=project,comments=comments)

# Define user_is_logged_in_as_guide function
def user_is_logged_in_as_guide():
    return 'username' in session and session['role'] == 'guide'

# Define user_is_logged_in_as_team_member function
def user_is_logged_in_as_team_member():
    return 'username' in session and session['role'] == 'student'

# Define project_belongs_to_guide function
def project_belongs_to_guide(project_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM assign_projects WHERE guide_id = %s AND project_id = %s", (session['id'], project_id))
    project = cursor.fetchone()
    cursor.close()
    return project is not None

# Define project_belongs_to_team_member function
def project_belongs_to_team_member(project_id):
    if 'id' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM assign_projects WHERE (team_leader_id = %s OR student1_id = %s OR student2_id = %s OR student3_id = %s OR student4_id = %s) AND project_id = %s", (session['id'], session['id'], session['id'], session['id'], session['id'], project_id))
        project = cursor.fetchone()
        cursor.close()
        return project is not None
    else:
        return False

# Define task_belongs_to_team_member function
def task_belongs_to_team_member(task_id):
    if 'id' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT tasks.* FROM tasks INNER JOIN assign_projects ON tasks.project_id = assign_projects.project_id WHERE (assign_projects.team_leader_id = %s OR assign_projects.student1_id = %s OR assign_projects.student2_id = %s OR assign_projects.student3_id = %s OR assign_projects.student4_id = %s) AND tasks.id = %s",  (session['id'], session['id'], session['id'], session['id'], session['id'], task_id))
        task = cursor.fetchone()
        cursor.close()
        return task is not None
    else:
        return False
    
# Define task_belongs_to_guide function
def task_belongs_to_guide(task_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s AND project_id IN (SELECT project_id FROM assign_projects WHERE guide_id = %s)", (task_id, session['id']))
    task = cursor.fetchone()
    cursor.close()
    return task is not None

    
@app.route('/guide/add-task/<int:project_id>', methods=['GET', 'POST'])
def guide_add_task(project_id):
    form = AddTaskForm()

    if user_is_logged_in_as_guide():
        if request.method == 'POST':
            if form.validate_on_submit():
                task_name = form.task_name.data
                task_description = form.task_description.data
                task_deadline = form.task_deadline.data
                start_date = form.start_date.data
                end_date = form.end_date.data
                
                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO tasks (project_id, name, description, deadline, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s)",
                               (project_id, task_name, task_description, task_deadline, start_date, end_date))
                mysql.connection.commit()
                cursor.close()
                    
                return redirect(url_for('guide_view_tasks', project_id=project_id))
        else:
            return render_template('guide/add_task.html', project_id=project_id, form=form)
    else:
        return redirect(url_for('guide_login'))

@app.route('/guide/view-tasks/<int:project_id>')
def guide_view_tasks(project_id):
    if user_is_logged_in_as_guide():
        if project_belongs_to_guide(project_id):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM tasks WHERE project_id = %s", (project_id,))
            tasks = cursor.fetchall()
            cursor.close()
            form = AddTaskForm()
            return render_template('guide/view_tasks.html', tasks=tasks, form=form, project_id=project_id)
        else:
            return "You are not authorized to access this project."
    else:
        return redirect(url_for('guide_login'))


@app.route('/guide/delete-task/<int:task_id>/<int:project_id>', methods=['POST'])
def guide_delete_task(task_id, project_id):
    if user_is_logged_in_as_guide():
        if task_belongs_to_guide(task_id):
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            mysql.connection.commit()
            cursor.close()
            flash('Task deleted successfully', 'success')
            return redirect(url_for('guide_view_tasks', project_id=project_id))
        else:
            return "You are not authorized to delete this task."
    else:
        return redirect(url_for('guide_login'))


# Route for guide to generate task report with a graph
@app.route('/guide/generate-report/<int:project_id>')
def guide_generate_task_report(project_id):
    if user_is_logged_in_as_guide(): 
        if project_belongs_to_guide(project_id): 
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT name, task_status FROM tasks WHERE project_id = %s", (project_id,))
            tasks_data = cursor.fetchall()
            cursor.close()

            # Extracting data for plotting
            valid_tasks_data = [task for task in tasks_data if task['task_status'] is not None]
            statuses = [task['task_status'] for task in valid_tasks_data]
            task_names = [task['name'] for task in valid_tasks_data]

            # Extracting unique statuses for plotting
            unique_statuses = list(set(statuses))

            # Count occurrences of each status
            counts = [statuses.count(status) for status in unique_statuses]

            # Plotting
            plt.figure(figsize=(8, 6))
            plt.bar(unique_statuses, counts, color='skyblue')  # Use unique statuses as x-axis
            plt.xlabel('Task Status')
            plt.ylabel('Number of Tasks')
            plt.title('Task Status Report')

            # Saving the plot as bytes
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)

            # Embedding the plot in the HTML response
            plot_url = base64.b64encode(img.getvalue()).decode()

            # Pass the tasks_data and plot_url to the template
            return render_template('guide/report.html', tasks_data=valid_tasks_data, plot=f'<img src="data:image/png;base64,{plot_url}" />')
        else:
            return "You are not authorized to access this project."
    else:
        return redirect(url_for('guide_login'))
    
@app.route('/guide_generate_task_timeline_chart/<int:project_id>', methods=['GET'])
def guide_generate_task_timeline_chart(project_id):
    task_data = []
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("SELECT name, start_date, end_date, description FROM tasks WHERE project_id = %s", (project_id,))
        tasks = cursor.fetchall()
        for task in tasks:
            task_data.append({
                'name': task['name'],
                'start_date': task['start_date'].strftime('%Y-%m-%d'),
                'end_date': task['end_date'].strftime('%Y-%m-%d'),
                'description': task['description']
            })

        # Fetch the project
        cursor.execute("SELECT id, name FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()

    finally:
        cursor.close()

    return render_template('guide/task_timeline_chart.html', task_data=task_data, project=project, project_id=project_id)

#guide route for view students
@app.route('/guide/view-students')
def guide_view_students():
    if 'id' not in session:
        # Redirect to login if guide is not logged in
        return redirect(url_for('guide_login'))

    # Fetch students associated with the guide's ID from the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM students ')
    students = cursor.fetchall()
    cursor.close()

  
    form = ProjectAssignForm()

    return render_template('guide/view_students.html', students=students, form=form)

@app.route('/guide/change-password', methods=['GET', 'POST'])
def guide_change_password():
    if 'id' in session and session.get('role') == 'guide':
        form = ChangePasswordForm()

        if form.validate_on_submit():
            new_password = generate_password_hash(form.new_password.data)

            try:
                cursor = mysql.connection.cursor()
                cursor.execute("UPDATE guides SET password = %s WHERE id = %s", (new_password, session['id']))
                mysql.connection.commit()
                cursor.close()

                flash('Password changed successfully.', 'success')
                return redirect(url_for('guide_dashboard'))
            except Exception as e:
                flash('An error occurred while changing password: {}'.format(str(e)), 'error')
                return redirect(url_for('guide_change_password'))

        # Pass project_id to the template
        project_id = 1  # Replace 1 with the actual project_id
        return render_template('guide/change_password.html', form=form, project_id=project_id)
    else:
        flash('Please login as a guide to change your password.', 'error')
        return redirect(url_for('guide_login'))


# End of Guide routes

#-----------------------------------------------------------------------------------------#
# Student routes
# Student login routes
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM students WHERE username = %s', (username,))
        student = cursor.fetchone()
        cursor.close()

        if student and check_password_hash(student['password'], password):
            session['id'] = student['id'] 
            session['username'] = student['username']
            session['role'] = 'student'
            flash('Logged in successfully!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Incorrect username or password!', 'error')

    return render_template('student/login.html', form=form)

# Student logout routes
@app.route('/student/logout')
def student_logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Student routes for projects
@app.route('/student/projects')
def student_projects():
    if 'id' in session and session.get('role') == 'student':
        student_id = session['id']
        
        # Using MySQL cursor to fetch assigned projects
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT assign_projects.*, projects.name AS project_name
            FROM assign_projects
            JOIN projects ON assign_projects.project_id = projects.id
            WHERE assign_projects.team_leader_id = %s 
                  OR assign_projects.student1_id = %s 
                  OR assign_projects.student2_id = %s 
                  OR assign_projects.student3_id = %s 
                  OR assign_projects.student4_id = %s
            ''', (str(student_id),str(student_id), str(student_id), str(student_id), str(student_id)))

        assigned_projects = cursor.fetchall()
        cursor.close()

        if assigned_projects:
            project_id = assigned_projects[0]['project_id']
        else:
            project_id = None

        return render_template('student/projects.html', assigned_projects=assigned_projects, project_id=project_id)
    else:
        flash('Please login as a student to view assigned projects.', 'error')
        return redirect(url_for('student_login'))


# Student routes for update status
@app.route('/student/update-status/<int:project_id>', methods=['GET', 'POST'])
def student_update_status(project_id):
    if 'id' in session and session.get('role') == 'student':
        form = StatusUpdateForm()

        if form.validate_on_submit():
            status = form.status.data
            student_id = session['id']

            # Check if the current status is not completed
            cursor = mysql.connection.cursor()
            cursor.execute('''
                SELECT status FROM assign_projects
                WHERE project_id = %s AND team_leader_id = %s
            ''', (project_id, student_id))
            project = cursor.fetchone()
            
            if project:  # Check if project status is not None
                current_status = project[0]  # Accessing the status from the tuple
                cursor.close()

                if current_status != 'Completed':
                    cursor = mysql.connection.cursor()
                    cursor.execute('''
                        UPDATE assign_projects
                        SET status = %s
                        WHERE project_id = %s AND team_leader_id = %s
                    ''', (status, project_id, student_id))
                    mysql.connection.commit()
                    cursor.close()

                    flash('Project status updated successfully.', 'success')
                else:
                    flash('Project status is already completed. You cannot update the status.', 'error')
            else:
                flash('Project status not found.', 'error')
            
            return redirect(url_for('student_projects'))
    
        return render_template('student/update_status.html', form=form)
    else:
        flash('Please login as a student to update the status of assigned projects.', 'error')
        return redirect(url_for('student_login'))

@app.route('/student/view-tasks/<int:project_id>')
def student_view_tasks(project_id):
    if user_is_logged_in_as_team_member():
        if project_belongs_to_team_member(project_id):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM tasks WHERE project_id = %s", (project_id,))
            tasks = cursor.fetchall()
            cursor.close()

            form = TaskStatusForm() 

            return render_template('student/tasks.html', tasks=tasks, project_id=project_id, form=form)
        else:
            return "You are not authorized to access this project."
    else:
        return redirect(url_for('student_login'))
    
@app.route('/student/update-task-status/<int:project_id>/<int:task_id>', methods=['POST'])
def student_update_task_status(project_id, task_id):
    if user_is_logged_in_as_team_member():
        if task_belongs_to_team_member(task_id):
            status = request.form['status']
            
            # Update task status
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE tasks SET task_status = %s WHERE id = %s", (status, task_id))
            
            # If the task is marked as completed, update the end date
            if status == 'Completed':
                end_date = datetime.now().date()  # Get current date
                cursor.execute("UPDATE tasks SET end_date = %s WHERE id = %s", (end_date, task_id))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('student_view_tasks', project_id=project_id))

        else:
            return "You are not authorized to update this task."
    else:
        return redirect(url_for('student_login'))

@app.route('/student/change-password', methods=['GET', 'POST'])
def student_change_password():
    if 'id' in session and session.get('role') == 'student':
        form = ChangePasswordForm()

        if form.validate_on_submit():
            new_password = generate_password_hash(form.new_password.data)

            try:
                cursor = mysql.connection.cursor()
                cursor.execute("UPDATE students SET password = %s WHERE id = %s", (new_password, session['id']))
                mysql.connection.commit()
                cursor.close()

                flash('Password changed successfully.', 'success')
                return redirect(url_for('student_dashboard'))
            except Exception as e:
                flash('An error occurred while changing password: {}'.format(str(e)), 'error')
                return redirect(url_for('student_change_password'))

        # Pass project_id to the template
        project_id = 1  # Replace 1 with the actual project_id
        return render_template('student/change_password.html', form=form, project_id=project_id)
    else:
        flash('Please login as a student to change your password.', 'error')
        return redirect(url_for('student_login'))
    
# Route to fetch project completion data
@app.route('/project-completion-data')
def project_completion_data():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT projects.name AS project_name, assign_projects.status
        FROM projects 
        LEFT JOIN assign_projects ON projects.id = assign_projects.project_id
    ''')
    project_data = cursor.fetchall()
    cursor.close()

    completed_count = 0
    on_progress_count = 0
    not_started_count = 0

    for data in project_data:
        if data['status'] == 'Completed':
            completed_count += 1
        elif data['status'] == 'In Progress':
            on_progress_count += 1
        else:
            not_started_count += 1

    return jsonify({
        'completed': completed_count, 
        'on_progress': on_progress_count, 
        'not_started': not_started_count 
    })
 
@app.route('/monitoring-chart')
def admin_monitoring_chart():
    return render_template('admin/monitoring_chart.html')
 

if __name__ == '__main__':  
    app.run(debug=True)
