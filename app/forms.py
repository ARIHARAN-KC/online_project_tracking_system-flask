from flask_wtf import FlaskForm
from wtforms import FileField, IntegerField, StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Add Project')


class ProjectAssignForm(FlaskForm):
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int) 
    guide_id = SelectField('Guide', validators=[DataRequired()], coerce=str) 
    team_leader_id = SelectField('Team Leader', validators=[DataRequired()], coerce=str) 
    student1_id = SelectField('Student 1', validators=[DataRequired()], coerce=str) 
    student2_id = SelectField('Student 2', validators=[DataRequired()], coerce=str) 
    student3_id = SelectField('Student 3', validators=[DataRequired()], coerce=str) 
    student4_id = SelectField('Student 4', validators=[DataRequired()], coerce=str) 
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Assign') 

class CommentForm(FlaskForm):
    display_name = StringField('Display Name', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])


class GuideRegistrationForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired(), Regexp('^[a-zA-Z0-9]+$', message='ID must be alphanumeric')])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
class GuideAssignProjectForm(FlaskForm):
    project_id = SelectField('Project', validators=[DataRequired()], coerce=int) 
    guide_id = SelectField('Guide', validators=[DataRequired()], coerce=str) 
    student_id = SelectField('Student', validators=[DataRequired()], coerce=str) 
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    submit = SubmitField('Assign')

class AddTaskForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    task_description = TextAreaField('Task Description', validators=[DataRequired()])
    task_deadline = DateField('Task Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Task')


    
class TaskStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Status')

class MilestoneForm(FlaskForm):
    milestone_name = StringField('Milestone Name', validators=[DataRequired()])
    milestone_description = TextAreaField('Milestone Description')
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])

class DocumentForm(FlaskForm):
    file = FileField('Document', validators=[DataRequired()])

class StudentRegistrationForm(FlaskForm):
    id = StringField('ID', validators=[DataRequired(), Regexp('^[a-zA-Z0-9]+$', message='ID must be alphanumeric')])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class StatusUpdateForm(FlaskForm):
    status = StringField('Status', validators=[DataRequired()])
    submit = SubmitField('Update Status')

class UpdateStatusForm(FlaskForm):
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed')], validators=[DataRequired()])
    submit = SubmitField('Update Status')
    
class TaskStatusUpdateForm(FlaskForm):
    status = StringField('Status', validators=[DataRequired()])
    submit = SubmitField('Update Status')

class MessageForm(FlaskForm):
    sender_id = IntegerField('Sender ID', validators=[DataRequired()])
    recipient_id = IntegerField('Recipient ID', validators=[DataRequired()])
    project_id = IntegerField('Project ID', validators=[DataRequired()])
    message = StringField('Message', validators=[DataRequired()])   

class UploadForm(FlaskForm):
    file = FileField('CSV File', validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')


class ProjectTasksForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    task_status = StringField('Task Status', validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Task')