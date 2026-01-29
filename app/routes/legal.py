"""
Legal pages routes
"""
from flask import Blueprint, render_template

bp = Blueprint('legal', __name__, url_prefix='/legal')

@bp.route('/datenschutz')
def datenschutz():
    """Datenschutzerklärung (Privacy Policy)"""
    return render_template('legal/datenschutz.html', title='Datenschutzerklärung')

@bp.route('/impressum')
def impressum():
    """Impressum (Imprint)"""
    return render_template('legal/impressum.html', title='Impressum')

@bp.route('/agb')
def agb():
    """Allgemeine Geschäftsbedingungen (Terms of Service)"""
    return render_template('legal/agb.html', title='AGB')

@bp.route('/account-deletion')
def account_deletion():
    """Account deletion page"""
    # Check if user is logged in
    from flask import request
    user_logged_in = 'access_token' in request.cookies or request.headers.get('Authorization')
    
    return render_template('legal/account_deletion.html', 
                          title='Konto löschen',
                          user_logged_in=user_logged_in)
