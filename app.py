from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import qrcode
import json
import os
import uuid
from datetime import datetime, timedelta
import csv
import io
import traceback
from collections import defaultdict, Counter

app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_FOLDER'] = 'generated_cards'
app.config['SIGNATURE_FOLDER'] = 'static/signatures'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
os.makedirs(app.config['SIGNATURE_FOLDER'], exist_ok=True)

DB_FILE = 'database.json'

# Template configurations
TEMPLATES = {
    'corporate': {
        'name': 'Corporate Blue',
        'primary_color': '#1e3a8a',
        'secondary_color': '#3b82f6',
        'accent_color': '#f59e0b',
        'gradient_start': '#1e3a8a',
        'gradient_end': '#3b82f6',
        'text_color': '#ffffff',
        'label_color': '#94a3b8',
        'font_style': 'modern'
    },
    'student': {
        'name': 'Student Green',
        'primary_color': '#065f46',
        'secondary_color': '#10b981',
        'accent_color': '#fbbf24',
        'gradient_start': '#065f46',
        'gradient_end': '#10b981',
        'text_color': '#ffffff',
        'label_color': '#a7f3d0',
        'font_style': 'modern'
    },
    'visitor': {
        'name': 'Visitor Orange',
        'primary_color': '#9a3412',
        'secondary_color': '#f97316',
        'accent_color': '#fef08a',
        'gradient_start': '#9a3412',
        'gradient_end': '#f97316',
        'text_color': '#ffffff',
        'label_color': '#fed7aa',
        'font_style': 'modern'
    },
    'premium': {
        'name': 'Premium Gold',
        'primary_color': '#451a03',
        'secondary_color': '#d97706',
        'accent_color': '#fcd34d',
        'gradient_start': '#451a03',
        'gradient_end': '#d97706',
        'text_color': '#fffbeb',
        'label_color': '#fde68a',
        'font_style': 'elegant'
    }
}

def init_db():
    """Initialize JSON database"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({
                'holders': [],
                'settings': {
                    'default_signature': None,
                    'company_name': 'SmartID Corporation',
                    'company_address': '123 Business Ave, Tech City'
                },
                'analytics': {
                    'card_generations': [],
                    'logins': []
                }
            }, f, indent=2)

def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'holders': [], 'settings': {}, 'analytics': {}}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/templates', methods=['GET'])
def get_templates():
    return jsonify(TEMPLATES)

@app.route('/api/holders', methods=['GET'])
def get_holders():
    try:
        db = load_db()
        return jsonify(db['holders'])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/holders', methods=['POST'])
def add_holder():
    try:
        data = request.get_json()
        print("Received data:", data)
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        db = load_db()
        
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
        
        db['holders'].append(new_holder)
        save_db(db)
        
        return jsonify({'success': True, 'holder': new_holder})
    except Exception as e:
        print("Error:", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        db = load_db()
        holders = db['holders']
        
        # Current date for calculations
        today = datetime.now()
        
        # 1. Department Distribution
        dept_counts = Counter([h.get('department', 'Unassigned') for h in holders])
        department_distribution = [{'name': dept, 'count': count} for dept, count in dept_counts.items()]
        
        # 2. Template Usage
        template_counts = Counter([h.get('template', 'corporate') for h in holders])
        template_usage = []
        for template_id, count in template_counts.items():
            template_info = TEMPLATES.get(template_id, TEMPLATES['corporate'])
            template_usage.append({
                'name': template_info['name'],
                'count': count,
                'color': template_info['primary_color']
            })
        
        # 3. Monthly Card Creation (Last 6 months)
        monthly_data = defaultdict(int)
        for holder in holders:
            try:
                created_date = datetime.fromisoformat(holder.get('created_at', ''))
                month_key = created_date.strftime('%b %Y')
                monthly_data[month_key] += 1
            except:
                pass
        
        # Get last 6 months
        last_6_months = []
        for i in range(5, -1, -1):
            date = today - timedelta(days=30*i)
            month_key = date.strftime('%b %Y')
            last_6_months.append({
                'month': month_key,
                'count': monthly_data.get(month_key, 0)
            })
        
        # 4. Blood Group Distribution
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        blood_group_counts = Counter([h.get('blood_group', 'Not Specified') for h in holders])
        blood_group_distribution = [{'group': bg, 'count': blood_group_counts.get(bg, 0)} for bg in blood_groups if blood_group_counts.get(bg, 0) > 0]
        
        # 5. Valid Till Status (Expiring Soon)
        expiring_soon = 0
        expired = 0
        permanent = 0
        
        for holder in holders:
            valid_till = holder.get('valid_till', '')
            if valid_till.lower() == 'permanent':
                permanent += 1
            elif valid_till:
                # Simple expiry check (can be enhanced)
                if '2024' in valid_till or '2025' in valid_till:
                    expiring_soon += 1
        
        # 6. Recent Activity (Last 10 created cards)
        recent_cards = sorted(holders, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        recent_activity = []
        for card in recent_cards:
            recent_activity.append({
                'name': card.get('full_name', 'Unknown'),
                'department': card.get('department', 'Unknown'),
                'template': TEMPLATES.get(card.get('template', 'corporate'), TEMPLATES['corporate'])['name'],
                'date': card.get('created_at', '')[:10] if card.get('created_at') else 'Unknown'
            })
        
        # 7. Template Popularity Trend
        template_trend = []
        for template_id, template_info in TEMPLATES.items():
            count = template_counts.get(template_id, 0)
            percentage = (count / len(holders) * 100) if holders else 0
            template_trend.append({
                'name': template_info['name'],
                'count': count,
                'percentage': round(percentage, 1),
                'color': template_info['primary_color']
            })
        
        # 8. Department Performance
        top_departments = sorted(department_distribution, key=lambda x: x['count'], reverse=True)[:5]
        
        analytics_data = {
            'summary': {
                'total_cards': len(holders),
                'total_departments': len(dept_counts),
                'total_templates': len(TEMPLATES),
                'expiring_soon': expiring_soon,
                'expired': expired,
                'permanent': permanent,
                'active_rate': round((len(holders) / max(1, len(holders))) * 100, 1)
            },
            'charts': {
                'department_distribution': department_distribution,
                'template_usage': template_usage,
                'monthly_creation': last_6_months,
                'blood_group_distribution': blood_group_distribution,
                'template_trend': template_trend,
                'top_departments': top_departments
            },
            'recent_activity': recent_activity,
            'growth_metrics': {
                'this_month': monthly_data.get(today.strftime('%b %Y'), 0),
                'last_month': monthly_data.get((today - timedelta(days=30)).strftime('%b %Y'), 0),
                'growth_percentage': calculate_growth(monthly_data, today)
            }
        }
        
        return jsonify(analytics_data)
    except Exception as e:
        print("Analytics error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

def calculate_growth(monthly_data, today):
    """Calculate month-over-month growth"""
    this_month = monthly_data.get(today.strftime('%b %Y'), 0)
    last_month = monthly_data.get((today - timedelta(days=30)).strftime('%b %Y'), 0)
    if last_month == 0:
        return 100 if this_month > 0 else 0
    return round(((this_month - last_month) / last_month) * 100, 1)

@app.route('/api/analytics/department/<dept_name>', methods=['GET'])
def get_department_analytics(dept_name):
    """Get detailed analytics for a specific department"""
    try:
        db = load_db()
        holders = [h for h in db['holders'] if h.get('department') == dept_name]
        
        # Department-specific analytics
        template_usage = Counter([h.get('template', 'corporate') for h in holders])
        blood_groups = Counter([h.get('blood_group', 'Not Specified') for h in holders])
        
        return jsonify({
            'department': dept_name,
            'total_members': len(holders),
            'template_breakdown': dict(template_usage),
            'blood_group_breakdown': dict(blood_groups),
            'members': holders
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/export-report', methods=['GET'])
def export_analytics_report():
    """Export analytics as CSV report"""
    try:
        db = load_db()
        holders = db['holders']
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Summary Report
        writer.writerow(['=== ID CARD MANAGEMENT SYSTEM REPORT ==='])
        writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([])
        
        writer.writerow(['=== SUMMARY STATISTICS ==='])
        writer.writerow(['Total ID Cards', len(holders)])
        writer.writerow(['Total Departments', len(set([h.get('department') for h in holders if h.get('department')]))])
        writer.writerow([])
        
        writer.writerow(['=== DEPARTMENT WISE BREAKDOWN ==='])
        dept_counts = Counter([h.get('department', 'Unassigned') for h in holders])
        for dept, count in dept_counts.items():
            writer.writerow([dept, count])
        writer.writerow([])
        
        writer.writerow(['=== TEMPLATE USAGE ==='])
        template_counts = Counter([h.get('template', 'corporate') for h in holders])
        for template, count in template_counts.items():
            writer.writerow([TEMPLATES.get(template, {}).get('name', template), count])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'analytics_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/holders/<holder_id>', methods=['DELETE'])
def delete_holder(holder_id):
    try:
        db = load_db()
        db['holders'] = [h for h in db['holders'] if h['id'] != holder_id]
        save_db(db)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo uploaded'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        img = Image.open(file)
        min_dim = min(img.size)
        left = (img.width - min_dim) / 2
        top = (img.height - min_dim) / 2
        img_cropped = img.crop((left, top, left + min_dim, top + min_dim))
        img_resized = img_cropped.resize((300, 300), Image.Resampling.LANCZOS)
        img_resized.save(filepath, quality=85)
        
        return jsonify({'photo_url': f'/static/uploads/{filename}'})
    except Exception as e:
        print("Error uploading photo:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-signature', methods=['POST'])
def upload_signature():
    try:
        if 'signature' not in request.files:
            return jsonify({'error': 'No signature uploaded'}), 400
        
        file = request.files['signature']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
        filename = f"sig_{uuid.uuid4()}.{ext}"
        filepath = os.path.join(app.config['SIGNATURE_FOLDER'], filename)
        
        img = Image.open(file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.thumbnail((200, 80), Image.Resampling.LANCZOS)
        img.save(filepath, 'PNG')
        
        return jsonify({'signature_url': f'/static/signatures/{filename}'})
    except Exception as e:
        print("Error uploading signature:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    try:
        db = load_db()
        return jsonify(db.get('settings', {}))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json()
        db = load_db()
        db['settings'] = data
        save_db(db)
        return jsonify({'success': True, 'settings': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-default-signature', methods=['POST'])
def upload_default_signature():
    try:
        if 'signature' not in request.files:
            return jsonify({'error': 'No signature uploaded'}), 400
        
        file = request.files['signature']
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        filename = f"default_signature.png"
        filepath = os.path.join(app.config['SIGNATURE_FOLDER'], filename)
        
        img = Image.open(file)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img.thumbnail((200, 80), Image.Resampling.LANCZOS)
        img.save(filepath, 'PNG')
        
        db = load_db()
        db['settings']['default_signature'] = f'/static/signatures/{filename}'
        save_db(db)
        
        return jsonify({'success': True, 'signature_url': f'/static/signatures/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-card/<holder_id>', methods=['GET'])
def generate_card(holder_id):
    try:
        db = load_db()
        holder = next((h for h in db['holders'] if h['id'] == holder_id), None)
        
        if not holder:
            return jsonify({'error': 'Holder not found'}), 404
        
        # Log card generation for analytics
        if 'analytics' not in db:
            db['analytics'] = {'card_generations': []}
        db['analytics']['card_generations'].append({
            'card_id': holder_id,
            'timestamp': datetime.now().isoformat(),
            'template': holder.get('template', 'corporate')
        })
        save_db(db)
        
        template = TEMPLATES.get(holder.get('template', 'corporate'), TEMPLATES['corporate'])
        
        card_width = 600
        card_height = 400
        
        img = Image.new('RGB', (card_width, card_height), color=template['primary_color'])
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([(0, 0), (card_width, 80)], fill=template['secondary_color'])
        draw.rectangle([(0, 320), (card_width, card_height)], fill=template['primary_color'])
        draw.rectangle([(0, 80), (10, 320)], fill=template['accent_color'])
        
        try:
            font_title = ImageFont.truetype("arial.ttf", 24)
            font_normal = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_normal = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((card_width//2, 15), template['name'].upper() + " ID CARD", fill=template['text_color'], anchor='mt', font=font_title)
        
        if holder.get('photo') and holder['photo']:
            try:
                photo_path = holder['photo'].replace('/static/', 'static/')
                if os.path.exists(photo_path):
                    photo = Image.open(photo_path)
                    photo = photo.resize((120, 120), Image.Resampling.LANCZOS)
                    bordered_photo = Image.new('RGB', (126, 126), 'white')
                    bordered_photo.paste(photo, (3, 3))
                    img.paste(bordered_photo, (37, 97))
                else:
                    draw.rectangle([(40, 100), (160, 220)], fill='#475569', outline=template['accent_color'], width=2)
                    draw.text((100, 160), "NO PHOTO", fill=template['text_color'], anchor='mm', font=font_small)
            except:
                draw.rectangle([(40, 100), (160, 220)], fill='#475569', outline=template['accent_color'], width=2)
                draw.text((100, 160), "NO PHOTO", fill=template['text_color'], anchor='mm', font=font_small)
        else:
            draw.rectangle([(40, 100), (160, 220)], fill='#475569', outline=template['accent_color'], width=2)
            draw.text((100, 160), "NO PHOTO", fill=template['text_color'], anchor='mm', font=font_small)
        
        start_x = 200
        start_y = 110
        line_height = 30
        
        valid_till = holder.get('valid_till', '')
        if not valid_till or valid_till == '':
            valid_till = 'Not Specified'
        
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
        
        qr_data = f"ID:{holder.get('employee_id', 'N/A')}|Name:{holder.get('full_name', 'N/A')}|Dept:{holder.get('department', 'N/A')}|Valid Till:{valid_till}"
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((80, 80))
        img.paste(qr_img, (card_width - 110, card_height - 100))
        
        signature_added = False
        if holder.get('signature') and holder['signature']:
            try:
                sig_path = holder['signature'].replace('/static/', 'static/')
                if os.path.exists(sig_path):
                    signature_img = Image.open(sig_path)
                    if signature_img.mode != 'RGBA':
                        signature_img = signature_img.convert('RGBA')
                    signature_img.thumbnail((150, 60), Image.Resampling.LANCZOS)
                    img.paste(signature_img, (start_x, card_height - 55), signature_img)
                    signature_added = True
            except Exception as e:
                print(f"Error adding custom signature: {e}")
        
        if not signature_added and holder.get('use_default_signature', False):
            db_settings = load_db()
            default_sig = db_settings.get('settings', {}).get('default_signature')
            if default_sig:
                try:
                    sig_path = default_sig.replace('/static/', 'static/')
                    if os.path.exists(sig_path):
                        signature_img = Image.open(sig_path)
                        if signature_img.mode != 'RGBA':
                            signature_img = signature_img.convert('RGBA')
                        signature_img.thumbnail((150, 60), Image.Resampling.LANCZOS)
                        img.paste(signature_img, (start_x, card_height - 55), signature_img)
                        signature_added = True
                except Exception as e:
                    print(f"Error adding default signature: {e}")
        
        if not signature_added:
            draw.line([(start_x, card_height - 40), (start_x + 150, card_height - 40)], fill=template['accent_color'], width=2)
            draw.text((start_x + 75, card_height - 35), "AUTHORIZED SIGNATURE", fill=template['label_color'], anchor='mt', font=font_small)
        
        card_filename = f"card_{holder_id}.png"
        card_path = os.path.join(app.config['GENERATED_FOLDER'], card_filename)
        img.save(card_path)
        
        return send_file(card_path, mimetype='image/png')
    except Exception as e:
        print("Error generating card:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/bulk-import', methods=['POST'])
def bulk_import():
    try:
        data = request.get_json()
        print("Bulk import data:", data)
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        db = load_db()
        
        imported = []
        for item in data.get('holders', []):
            new_holder = {
                'id': str(uuid.uuid4())[:8],
                'full_name': item.get('full_name', ''),
                'employee_id': item.get('employee_id', ''),
                'department': item.get('department', ''),
                'designation': item.get('designation', ''),
                'email': item.get('email', ''),
                'phone': item.get('phone', ''),
                'blood_group': item.get('blood_group', ''),
                'valid_till': item.get('valid_till', ''),
                'photo': '',
                'signature': '',
                'use_default_signature': item.get('use_default_signature', False),
                'template': item.get('template', 'corporate'),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            db['holders'].append(new_holder)
            imported.append(new_holder)
        
        save_db(db)
        return jsonify({'success': True, 'imported': imported, 'count': len(imported)})
    except Exception as e:
        print("Error in bulk import:", traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-csv', methods=['GET'])
def export_csv():
    try:
        db = load_db()
        holders = db['holders']
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Full Name', 'Employee ID', 'Department', 'Designation', 'Email', 'Phone', 'Blood Group', 'Valid Till', 'Template', 'Has Signature', 'Created Date'])
        
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
                'Yes' if holder.get('signature') or holder.get('use_default_signature') else 'No',
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)