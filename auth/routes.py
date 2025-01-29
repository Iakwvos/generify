from flask import render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from . import auth_bp
from supabase import create_client, Client
from config import Config
from datetime import datetime

# Initialize Supabase client
supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Sign in user with Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Get the user data
            user = auth_response.user
            
            if not user:
                raise Exception("Invalid credentials")
            
            # Store user session
            session['user'] = {
                'id': user.id,
                'email': user.email,
                'first_name': user.user_metadata.get('first_name'),
                'last_name': user.user_metadata.get('last_name'),
                'access_token': auth_response.session.access_token
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Logged in successfully!', 'redirect': url_for('main.dashboard')})
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)})
            flash('Invalid email or password', 'error')
            return redirect(url_for('main.landing'))
    
    # For GET requests with modal parameter, return the modal content
    if request.args.get('modal'):
        return render_template('auth/login_modal.html')
        
    # Otherwise redirect to landing with modal parameter
    return redirect(url_for('main.landing', open_modal='login'))

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # If user is already logged in, redirect to dashboard
    if 'user' in session:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        try:
            # Create user in Supabase Auth with auto-confirm
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "email_confirmed": True,
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": phone
                    }
                }
            })
            
            # Get the user data
            user = auth_response.user
            
            if not user:
                raise Exception("Failed to create user account")
            
            try:
                # Try to insert into users table
                user_data = {
                    'id': user.id,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone
                }
                data = supabase.table('users').insert(user_data).execute()
            except Exception as insert_error:
                # If error is duplicate key, we can proceed (user already exists)
                if not str(insert_error).startswith("{'code': '23505'"):
                    raise insert_error
            
            # Store user session
            session['user'] = {
                'id': user.id,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'access_token': auth_response.session.access_token
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Account created successfully!', 'redirect': url_for('main.dashboard')})
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)})
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('main.landing'))
    
    # For GET requests with modal parameter, return the modal content
    if request.args.get('modal'):
        return render_template('auth/signup_modal.html')
        
    # Otherwise redirect to landing with modal parameter
    return redirect(url_for('main.landing', open_modal='signup'))

@auth_bp.route('/logout')
def logout():
    try:
        # Sign out from Supabase
        supabase.auth.sign_out()
        session.clear()
        flash('Successfully logged out!', 'success')
    except Exception as e:
        flash('Error logging out', 'error')
    
    return redirect(url_for('main.landing'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        try:
            supabase.auth.reset_password_email(email)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Password reset instructions sent to your email!'})
            flash('Password reset instructions sent to your email!', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Error sending reset instructions'})
            flash('Error sending reset instructions', 'error')
    
    # Check if this is a modal request
    if request.args.get('modal'):
        return render_template('auth/reset_password_modal.html')
    return render_template('auth/reset_password.html') 