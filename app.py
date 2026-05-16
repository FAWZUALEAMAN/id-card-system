# ============ SIMPLIFIED VERCEL-FRIENDLY VERSION ============
import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Simple in-memory storage for Vercel (since file writes don't persist)
# For demo purposes only - use a real database for production
holders = []
settings = {
    'default_signature': None,
    'company_name': 'ID Swift Corporation'
}

# Template configurations
TEMPLATES = {
    'corporate': {
        'name': 'Corporate Blue',
        'primary_color': '#1e3a8a',
        'secondary_color': '#3b82f6',
        'accent_color': '#f59e0b',
        'text_color': '#ffffff',
        'label_color': '#94a3b8'
    },
    'student': {
        'name': 'Student Green',
        'primary_color': '#065f46',
        'secondary_color': '#10b981',
        'accent_color': '#fbbf24',
        'text_color': '#ffffff',
        'label_color': '#a7f3d0'
    },
    'visitor': {
        'name': 'Visitor Orange',
        'primary_color': '#9a3412',
        'secondary_color': '#f97316',
        'accent_color': '#fef08a',
        'text_color': '#ffffff',
        'label_color': '#fed7aa'
    },
    'premium': {
        'name': 'Premium Gold',
        'primary_color': '#451a03',
        'secondary_color': '#d97706',
        'accent_color': '#fcd34d',
        'text_color': '#fffbeb',
        'label_color': '#fde68a'
    }
}

# ============ HELPER FUNCTIONS ============
def load_data():
    global holders, settings
    # For Vercel, use in-memory storage
    # In production, connect to a database like MongoDB, Supabase, or Upstash Redis

def save_data():
    global holders, settings
    # For Vercel, data stays in memory
    # In production, save to database
    pass

# Initialize data
load_data()

# Add sample data if empty
if not holders:
    holders.append({
        'id': 'sample001',
        'full_name': 'John Doe',
        'employee_id': 'EMP001',
        'department': 'Information Technology',
        'designation': 'Software Engineer',
        'email': 'john.doe@example.com',
        'phone': '+1234567890',
        'blood_group': 'A+',
        'valid_till': 'December 2025',
        'photo': '',
        'signature': '',
        'use_default_signature': False,
        'template': 'corporate',
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    })

# ============ ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/templates', methods=['GET'])
def get_templates():
    return jsonify(TEMPLATES)

@app.route('/api/holders', methods=['GET'])
def get_holders():
    try:
        return jsonify(holders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/holders', methods=['POST'])
def add_holder():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        new_holder = {
            'id': str(uuid.uuid4())[:8],
            'full_name': data.get('full_name', ''),
            'employee_id': data.get('employee_id', ''),
            'department': data.get('department', ''),
            'designation': data.get('designation', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'blood_group': data.get('blood_group', ''),
            'valid_till': data.get('valid_till', ''),
            'photo': data.get('photo', ''),
            'signature': data.get('signature', ''),
            'use_default_signature': data.get('use_default_signature', False),
            'template': data.get('template', 'corporate'),
            'created_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        holders.append(new_holder)
        save_data()
        
        return jsonify({'success': True, 'holder': new_holder})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/holders/<holder_id>', methods=['DELETE'])
def delete_holder(holder_id):
    try:
        global holders
        holders = [h for h in holders if h['id'] != holder_id]
        save_data()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    try:
        from collections import Counter
        
        dept_counts = Counter([h.get('department', 'Unassigned') for h in holders])
        template_counts = Counter([h.get('template', 'corporate') for h in holders])
        
        return jsonify({
            'summary': {
                'total_cards': len(holders),
                'total_departments': len(dept_counts),
                'total_templates': 4,
                'active_rate': 100 if holders else 0
            },
            'charts': {
                'department_distribution': [{'name': k, 'count': v} for k, v in dept_counts.items()],
                'template_usage': [{'name': TEMPLATES.get(k, {}).get('name', k), 'count': v, 'color': TEMPLATES.get(k, {}).get('primary_color', '#000')} for k, v in template_counts.items()],
                'monthly_creation': [],
                'blood_group_distribution': [],
                'template_trend': []
            },
            'recent_activity': [
                {
                    'name': h.get('full_name', 'Unknown'),
                    'department': h.get('department', 'Unknown'),
                    'template': TEMPLATES.get(h.get('template', 'corporate'), {}).get('name', 'Unknown'),
                    'date': h.get('created_at', '')[:10] if h.get('created_at') else 'Unknown'
                } for h in holders[-5:]
            ],
            'growth_metrics': {
                'this_month': len(holders),
                'last_month': 0,
                'growth_percentage': 0
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-card/<holder_id>', methods=['GET'])
def generate_card(holder_id):
    try:
        # Import PIL here to avoid startup issues
        from PIL import Image, ImageDraw, ImageFont
        import qrcode
        
        holder = next((h for h in holders if h['id'] == holder_id), None)
        
        if not holder:
            return jsonify({'error': 'Holder not found'}), 404
        
        template = TEMPLATES.get(holder.get('template', 'corporate'), TEMPLATES['corporate'])
        
        # Create ID Card
        card_width = 600
        card_height = 400
        
        img = Image.new('RGB', (card_width, card_height), color=template['primary_color'])
        draw = ImageDraw.Draw(img)
        
        # Add stripes
        draw.rectangle([(0, 0), (card_width, 80)], fill=template['secondary_color'])
        draw.rectangle([(0, 320), (card_width, card_height)], fill=template['primary_color'])
        draw.rectangle([(0, 80), (10, 320)], fill=template['accent_color'])
        
        # Font handling
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_normal = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Title
        draw.text((card_width//2, 15), template['name'].upper() + " ID CARD", fill=template['text_color'], anchor='mt', font=font_title)
        
        # Photo placeholder
        draw.rectangle([(40, 100), (160, 220)], fill='#475569', outline=template['accent_color'], width=2)
        draw.text((100, 160), "PHOTO", fill=template['text_color'], anchor='mm', font=font_small)
        
        # Details
        start_x = 200
        start_y = 110
        line_height = 30
        
        valid_till = holder.get('valid_till', 'Not Specified')
        
        details = [
            ('NAME', holder.get('full_name', 'N/A').upper()),
            ('ID NO', holder.get('employee_id', 'N/A')),
            ('DEPARTMENT', holder.get('department', 'N/A')),
            ('DESIGNATION', holder.get('designation', 'N/A')),
            ('BLOOD GROUP', holder.get('blood_group', 'N/A')),
            ('VALID TILL', valid_till)
        ]
        
        for i, (label, value) in enumerate(details):
            y = start_y + (i * line_height)
            draw.text((start_x, y), f"{label}:", fill=template['label_color'], font=font_small)
            draw.text((start_x + 120, y), str(value), fill=template['text_color'], font=font_normal)
        
        # QR Code
        qr_data = f"ID:{holder.get('employee_id', 'N/A')}|Name:{holder.get('full_name', 'N/A')}"
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((80, 80))
        img.paste(qr_img, (card_width - 110, card_height - 100))
        
        # Signature line
        draw.line([(start_x, card_height - 40), (start_x + 150, card_height - 40)], fill=template['accent_color'], width=2)
        draw.text((start_x + 75, card_height - 35), "AUTHORIZED SIGNATURE", fill=template['label_color'], anchor='mt', font=font_small)
        
        # Save to bytes
        import io
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', download_name=f'id_card_{holder_id}.png')
    except Exception as e:
        print(f"Error generating card: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    try:
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Full Name', 'Employee ID', 'Department', 'Designation', 'Email', 'Phone', 'Blood Group', 'Valid Till', 'Template', 'Created Date'])
        
        for holder in holders:
            writer.writerow([
                holder.get('full_name', ''),
                holder.get('employee_id', ''),
                holder.get('department', ''),
                holder.get('designation', ''),
                holder.get('email', ''),
                holder.get('phone', ''),
                holder.get('blood_group', ''),
                holder.get('valid_till', ''),
                holder.get('template', 'corporate'),
                holder.get('created_at', '')
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='id_cards_export.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ HEALTH CHECK ============
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ============ FOR LOCAL DEVELOPMENT ============
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
