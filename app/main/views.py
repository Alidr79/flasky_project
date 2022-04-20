import datetime
import os

from flask import render_template, session, redirect, url_for, current_app
from . import main
from .forms import NameForm
from ..email import send_mail
import sqlite3
from flask import request
from flask import flash
from ..database import get_connection
from .. import login_manager
from ..user import User

from flask_login import login_required, login_user, logout_user, current_user
from ..user import load_user
from werkzeug.utils import secure_filename
from flask import send_from_directory

from .. import time_from


@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    connection = get_connection().get_db_connection()
    if request.method == "POST":
        # unconfirmed users can't send post :
        if get_connection().is_confirmed(current_user.get_username()) == 0:
            flash("You can't send posts until you confirm your account")
            return redirect(url_for('main.index'))

        post_body = request.form['post_body']
        if post_body.count('\n') > 4:  # prevent line abuse :)
            # number of \n = number of lines - 1
            flash("Sorry, your post must contain less than 5 lines.")
            return redirect(url_for('main.index'))

        connection.execute("INSERT INTO post(body,author_id) VALUES(?,?)",
                           (post_body, current_user.get_id()))
        connection.commit()
        flash('Post has been sent successfully.')
        return redirect(url_for('main.index'))

    page_number = request.args.get('page', 1, type=int)
    LIMIT = 10
    offset = (page_number - 1) * LIMIT

    # number of pages
    num_post = connection.execute("SELECT COUNT(id) AS num FROM post").fetchone()
    page_float = num_post['num'] / LIMIT
    page_int = int(num_post['num'] / LIMIT)

    total_pages = page_int
    if (page_float - page_int) > 0:
        total_pages = page_int + 1

    next_page = request.args.get('page', 1, type= int)+1
    previous_page = request.args.get('page', 1, type= int)-1

    posts = connection.execute("SELECT post.body,"
                               + "datetime(post.timestamp, 'localtime') AS timestamp"
                               + ", user.id, user.username, user.nick_name " +
                               "FROM post " +
                               "INNER JOIN user ON post.author_id=user.id " +
                               "ORDER BY post.timestamp DESC "
                               "LIMIT ? OFFSET ? ;",
                               (LIMIT, offset)).fetchall()
    connection.close()
    username = current_user.get_username()
    return render_template('index.html', username=username, posts=posts,
                           total_pages = total_pages, next_page = next_page,
                           previous_page = previous_page)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        status, user = get_connection().verify_password(request.form['username'],
                                                        request.form['password'])
        if status == 1:  # Valid user
            user_obj = load_user(user['id'])
            login_user(user_obj, remember=('remember' in request.form.getlist("remember")))
            print('Logged in successfully ')
            return redirect(url_for('main.index'))
        elif status == 0:  # Incorrect password
            flash("Incorrect password!")
            return redirect(url_for("main.login"))
            print('Incorrect password')
        elif status == -1:  # User not found
            flash("User not found!")
            return redirect(url_for("main.login"))
            print("user not found")
    return render_template('login/index.html')


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('logged out')
    return redirect(url_for('main.index'))


@main.route('/signup', methods=['GET', 'POST'])
def signup():
    input_username = ''  # initialize

    if request.method == "POST":
        input_username = request.form['username']
        input_password = request.form['password']
        confirm_pass = request.form['confirm_password']

        # chek confirm password equality
        if input_password != confirm_pass:
            flash('Error in confirming the password!')
            return render_template('/signup/index.html', username=input_username)

        user_exist = get_connection().user_exist(input_username)

        if user_exist:
            flash("User exists!", 'danger')
            return redirect(url_for('main.signup'))

        if len(input_password) < 8 or len(input_password) > 16:
            flash('Password must have minimum of 8 and maximum of 16 characters!')
            return redirect(url_for('main.signup'))

        else:
            add_status = get_connection().add_user(input_username, input_password)
            if not add_status:
                flash("Error occurred")
                return render_template('/signup/index.html', username=input_username)
            else:
                token = get_connection().generate_confirmation_token(input_username)
                send_mail(input_username, ' Confirm your email', 'mail/confirm_mail', token=token)
                connection = get_connection().get_db_connection()
                user = connection.execute("SELECT * FROM user WHERE username=?",
                                          [input_username]).fetchone()

                # important you should login the user here otherwise it can't open main.index
                user_obj = load_user(user['id'])
                login_user(user_obj, remember=('remember' in request.form.getlist("remember")))

                flash('The confirmation message has been sent to your email')
                return redirect(url_for('main.index'))

    return render_template('/signup/index.html', username=input_username)


@main.route('/confirm/<token>')
@login_required
def confirm(token):
    try:
        username = get_connection().confirm_token(token)
    except:
        flash("The confirmation link is invalid or expired")

    connection = get_connection().get_db_connection()
    user = connection.execute("SELECT * FROM user WHERE username=?",
                              [username]).fetchone()

    if user is None:
        connection.close()
        flash('The confirmation link is invalid or expired')
        return redirect(url_for('main.index'))

    if user['is_confirmed']:
        connection.close()
        flash('This account has been already confirmed.')

    elif not user['is_confirmed']:
        connection.execute("UPDATE user SET is_confirmed=1 WHERE username=?",
                           [username])
        connection.commit()
        connection.close()
        flash('you have confirmed your email, Thanks!')

    return redirect(url_for('main.index'))


@main.route('/profile/<username>')
def profile(username):
    owner = False
    if current_user.get_username() == username:
        owner = True
    connection = get_connection().get_db_connection()
    user = connection.execute("SELECT * FROM user WHERE username=?",
                              [username]).fetchone()

    last_seen_str = time_from(user['last_seen'])

    profile_pic = ('profile_pic_' + str(user['id']) + '.jpg')

    return render_template('profile/index.html', user=user, last_seen_str=last_seen_str,
                           profile_pic=profile_pic, owner=owner)


@main.route('/upload/<filename>')
def send_profile_pic(filename):
    return send_from_directory(current_app.config['PATH_PROFILE_IMAGES']
                               , filename)  # as_attachment=True


@main.route('/upload/_<user_id>')  # input shouldn't start with a number ....
def pic_from_id(user_id):
    filename = 'profile_pic_' + str(user_id) + '.jpg'
    return send_from_directory(current_app.config['PATH_PROFILE_IMAGES'],
                               filename)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    connection = get_connection().get_db_connection()
    user = connection.execute("SELECT * FROM user WHERE id=?",
                              [current_user.get_id()]).fetchone()
    if request.method == 'POST':
        username = current_user.get_username()
        connection.execute("UPDATE user SET nick_name=? , about=? WHERE username=?",
                           (request.form['nick_name'], request.form['about_me'], username))

        pic_file = request.files['profile_pic']
        if pic_file:
            # i will store this file as .jpg
            # no matter what is the original file format
            # WHY?
            # because it's easier and safer
            # easier, because profile picture format is always 'profile_pic_'+id+'.jpg
            # safer because with this approach if a user try to upload a new picture
            # the new one is replaced with the older picture (because of the same name)
            # so each user has only one file in static directory and we prevent
            # storage overflow ... maybe i change my opinion in future.
            file_name = ('profile_pic_' + str(current_user.get_id()) + '.jpg')
            pic_file.save(os.path.join(current_app.config['PATH_PROFILE_IMAGES'], file_name))
        connection.commit()
        connection.close()
        return redirect(url_for('main.profile', username=username))
    return render_template('profile/edit_profile.html', user=user)


@main.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == "POST":
        password = request.form['password']
        status, _ = get_connection().verify_password(current_user.get_username(), password)
        if status == 1:
            id = current_user.get_id()
            connection = get_connection().get_db_connection()
            connection.execute("DELETE FROM user WHERE id=?",
                               [id])
            connection.commit()
            connection.close()

            # remove profile picture
            profile_pic = os.path.join(current_app.config['PATH_STATIC'], 'profile_images',
                                       'profile_pic_' + str(id) + '.jpg')
            if os.path.exists(profile_pic):
                os.remove(profile_pic)

            flash('You have deleted your account!')
            return redirect(url_for('main.index'))
        else:
            flash("Incorrect password")
            return redirect(url_for('main.delete_account'))

    return render_template('profile/delete_account.html')


@main.before_app_request
def before_request():
    if current_user.is_authenticated:
        # update the last_seen of the current user
        get_connection().ping(current_user.get_username())


@main.route('/confirm')
@login_required
def resend():
    pass
