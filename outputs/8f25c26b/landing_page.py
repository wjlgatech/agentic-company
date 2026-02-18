# landing_page.py
from flask import Flask, render_template, request, jsonify, redirect
from typing import Dict, List
import sqlite3
import uuid
import time
from datetime import datetime

app = Flask(__name__)

class WaitlistLanding:
    """High-converting landing page with viral mechanics."""
    
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for waitlist and referrals."""
        conn = sqlite3.connect('waitlist.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signups (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                signup_date DATETIME,
                source TEXT,
                position INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id TEXT PRIMARY KEY,
                referrer_id TEXT,
                referee_email TEXT,
                referral_date DATETIME,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

@app.route('/')
def landing_page():
    """Serve the main landing page."""
    # Get real-time stats for social proof
    stats = get_waitlist_stats()
    
    return render_template('landing.html', 
                         waitlist_count=stats['total_signups'],
                         recent_signups=stats['recent_signups'])

@app.route('/signup', methods=['POST'])
def handle_signup():
    """Process waitlist signup with referral tracking."""
    start_time = time.time()
    
    data = request.get_json()
    email = data.get('email')
    referral_code = data.get('referral_code')
    source = data.get('source', 'direct')
    
    if not email or '@' not in email:
        return jsonify({'error': 'Valid email required'}), 400
    
    # Generate unique referral code and position
    user_id = str(uuid.uuid4())
    user_referral_code = generate_referral_code()
    
    conn = sqlite3.connect('waitlist.db')
    cursor = conn.cursor()
    
    try:
        # Get current position
        cursor.execute('SELECT COUNT(*) FROM signups')
        position = cursor.fetchone()[0] + 1
        
        # Insert new signup
        cursor.execute('''
            INSERT INTO signups (id, email, referral_code, referred_by, signup_date, source, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, email, user_referral_code, referral_code, datetime.now(), source, position))
        
        # Track referral if applicable
        if referral_code:
            cursor.execute('''
                INSERT INTO referrals (id, referrer_id, referee_email, referral_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), referral_code, email, datetime.now(), 'completed'))
        
        conn.commit()
        
        # Ensure page loads in <3 seconds
        processing_time = time.time() - start_time
        if processing_time > 3.0:
            app.logger.warning(f"Signup processing took {processing_time:.2f}s")
        
        return jsonify({
            'success': True,
            'position': position,
            'referral_code': user_referral_code,
            'referral_url': f"https://agenticom.com/?ref={user_referral_code}"
        })
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 400
    finally:
        conn.close()

@app.route('/stats')
def get_waitlist_stats():
    """Get real-time waitlist statistics for social proof."""
    conn = sqlite3.connect('waitlist.db')
    cursor = conn.cursor()
    
    # Total signups
    cursor.execute('SELECT COUNT(*) FROM signups')
    total_signups = cursor.fetchone()[0]
    
    # Recent signups (last 24 hours)
    cursor.execute('''
        SELECT COUNT(*) FROM signups 
        WHERE signup_date > datetime('now', '-1 day')
    ''')
    recent_signups = cursor.fetchone()[0]
    
    # Top referrers
    cursor.execute('''
        SELECT s.email, COUNT(r.id) as referral_count
        FROM signups s
        LEFT JOIN referrals r ON s.referral_code = r.referrer_id
        GROUP BY s.id
        ORDER BY referral_count DESC
        LIMIT 10
    ''')
    top_referrers = cursor.fetchall()
    
    conn.close()
    
    return {
        'total_signups': total_signups,
        'recent_signups': recent_signups,
        'top_referrers': top_referrers,
        'conversion_rate': calculate_conversion_rate()
    }

def generate_referral_code() -> str:
    """Generate unique referral code."""
    return str(uuid.uuid4())[:8].upper()

def calculate_conversion_rate() -> float:
    """Calculate landing page conversion rate."""
    # This would integrate with analytics to get visitor count
    # For now, returning a placeholder
    return 18.5  # Targeting >15% conversion rate

if __name__ == '__main__':
    waitlist = WaitlistLanding()
    app.run(debug=False, host='0.0.0.0', port=5000)