"""
Flask Web Application for AI-Powered Job Application Agent
Run on localhost for web interface
"""

import os
import sys
import json
import re
from typing import Tuple
from flask import Flask, render_template, request, jsonify, send_file, flash
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Import our modular components
from utils.llm_factory import create_llm_client
from utils.document_builder import DocumentBuilder
from utils.match_calculator import MatchCalculator
from utils.profile_deduplicator import ProfileDeduplicator
from utils.linkedin_importer import LinkedInImporter, import_linkedin_profile
from utils.history_store import HistoryStore
from agents.job_analyzer import JobAnalyzer
from agents.cv_customizer import CVCustomizer
from agents.cover_letter_generator import CoverLetterGenerator

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Global variables for initialized components
client = None
builder = None
match_calculator = None
job_analyzer = None
cv_customizer = None
cover_letter_generator = None
history_store = HistoryStore()

def initialize_components():
    """Initialize all AI components."""
    global client, builder, match_calculator, job_analyzer, cv_customizer, cover_letter_generator

    client = create_llm_client()
    builder = DocumentBuilder()
    match_calculator = MatchCalculator()
    job_analyzer = JobAnalyzer(client)
    cv_customizer = CVCustomizer(client)
    cover_letter_generator = CoverLetterGenerator(client)

def load_profile(path: str = "data/master_profile.json") -> dict:
    """Load the master profile JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Check if template exists
        template_path = path + ".template"
        if os.path.exists(template_path):
            raise FileNotFoundError(
                f"Profile file not found at {path}. "
                f"Please run 'python setup_profile.py' to create your profile, "
                f"or copy '{template_path}' to '{path}' and edit it with your information."
            )
        raise FileNotFoundError(
            f"Profile file not found at {path}. "
            f"Please run 'python setup_profile.py' to create your profile."
        )
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {path}")

def check_profile_setup() -> Tuple[bool, str]:
    """Check if profile is set up and not using template values."""
    try:
        profile = load_profile()
        name = profile.get('personal_info', {}).get('name', '')
        
        # Check if using template/default values
        if name in ['Your Full Name', 'Alex Candidate', '']:
            return False, "Profile exists but contains placeholder values. Please update with your information."
        
        return True, "Profile is set up correctly."
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error checking profile: {str(e)}"

def sanitize_filename(name: str) -> str:
    """Sanitize filename for Windows."""
    return re.sub(r'[<>:"/\\|?*]', '', name).strip().replace(' ', '_')

@app.route('/')
def index():
    """Main page."""
    try:
        profile = load_profile()
        profile_ready, message = check_profile_setup()
        
        # Use redesigned template if available, fallback to original
        try:
            return render_template('index_redesigned.html', 
                                 profile=profile if profile_ready else None,
                                 profile_warning=message if not profile_ready else None)
        except:
            return render_template('index.html', 
                                profile=profile if profile_ready else None,
                                profile_warning=message if not profile_ready else None)
    except Exception as e:
        flash(f"Error loading profile: {str(e)}", "error")
        try:
            return render_template('index_redesigned.html', profile=None, profile_warning=str(e))
        except:
            return render_template('index.html', profile=None, profile_warning=str(e))

@app.route('/api/profile/check', methods=['GET'])
def check_profile_endpoint():
    """Check if profile is set up."""
    try:
        is_ready, message = check_profile_setup()
        return jsonify({
            'ready': is_ready,
            'message': message
        })
    except Exception as e:
        return jsonify({
            'ready': False,
            'message': str(e)
        }), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get current profile."""
    try:
        profile = load_profile()
        # Remove sensitive data if needed
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def update_profile():
    """Update profile from web interface."""
    try:
        data = request.json
        profile = data.get('profile')
        
        if not profile:
            return jsonify({'success': False, 'error': 'No profile data provided'}), 400
        
        # Validate required fields
        if not profile.get('personal_info', {}).get('name'):
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        # Deduplicate before saving
        profile = ProfileDeduplicator.deduplicate_profile(profile)
        
        # Save profile
        os.makedirs("data", exist_ok=True)
        with open("data/master_profile.json", 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/linkedin/import', methods=['POST'])
def import_linkedin():
    """Import profile from LinkedIn export or URL."""
    try:
        data = request.json
        export_path = data.get('export_path')
        linkedin_url = data.get('linkedin_url')
        
        if not export_path and not linkedin_url:
            return jsonify({
                'success': False,
                'error': 'Either export_path or linkedin_url must be provided'
            }), 400
        
        # Import LinkedIn data
        profile = import_linkedin_profile(
            export_path=export_path,
            linkedin_url=linkedin_url
        )
        
        # Deduplicate imported data
        profile = ProfileDeduplicator.deduplicate_profile(profile)
        
        return jsonify({
            'success': True,
            'profile': profile,
            'message': 'LinkedIn profile imported successfully. Please review and complete any missing information.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/process', methods=['POST'])
def process_job():
    """Process job description and generate CV/cover letter."""
    try:
        data = request.json
        job_description = data.get('job_description', '').strip()
        
        if not job_description or len(job_description) < 50:
            return jsonify({
                'success': False,
                'error': 'Job description is too short. Please provide at least 50 characters.'
            }), 400
        
        # Check profile setup
        profile_ready, message = check_profile_setup()
        if not profile_ready:
            return jsonify({
                'success': False,
                'error': f'Profile not set up: {message}',
                'profile_required': True
            }), 400
        
        # Initialize components if not already done
        if client is None:
            initialize_components()
        
        # Load profile
        profile = load_profile()
        
        # Deduplicate profile first
        profile = ProfileDeduplicator.deduplicate_profile(profile)
        
        # Analyze job
        analysis = job_analyzer.analyze(job_description)
        role_title = analysis.get('role_info', {}).get('title', 'Unknown Role')
        company = analysis.get('role_info', {}).get('company', 'Unknown Company')
        
        # Calculate match score
        match_data = match_calculator.calculate_match_score(profile, analysis)
        
        # Customize CV
        customized_cv = cv_customizer.customize(profile, analysis)
        
        # Remove any repetitive content
        customized_cv = ProfileDeduplicator.remove_repetitive_content(customized_cv)
        
        # Generate cover letter
        cover_letter_text = cover_letter_generator.generate(profile, analysis)
        
        # Generate documents
        os.makedirs("output", exist_ok=True)
        safe_title = sanitize_filename(role_title)
        safe_company = sanitize_filename(company)
        
        cv_filename = f"output/CV_{safe_company}_{safe_title}.docx"
        cl_filename = f"output/CL_{safe_company}_{safe_title}.docx"
        cv_pdf_filename = f"output/CV_{safe_company}_{safe_title}.pdf"
        cl_pdf_filename = f"output/CL_{safe_company}_{safe_title}.pdf"

        # Create documents (reuse builder but create new instances for each)
        cv_builder = DocumentBuilder()
        cv_builder.create_cv(customized_cv, cv_filename)
        cv_builder.create_cv_pdf(customized_cv, cv_pdf_filename)

        cl_builder = DocumentBuilder()
        cl_builder.create_cover_letter(cover_letter_text, profile, cl_filename)
        cl_builder.create_cover_letter_pdf(cover_letter_text, profile, cl_pdf_filename)

        # Record this run in the local application history
        application_id = history_store.record_application(
            role_title=role_title,
            company=company,
            match_score=match_data.get('overall_score'),
            cv_file=cv_filename,
            cover_letter_file=cl_filename,
            analysis=analysis,
        )

        return jsonify({
            'success': True,
            'application_id': application_id,
            'role_title': role_title,
            'company': company,
            'match_score': match_data,
            'cv_file': cv_filename,
            'cover_letter_file': cl_filename,
            'cv_pdf_file': cv_pdf_filename,
            'cover_letter_pdf_file': cl_pdf_filename,
            'analysis': analysis
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Configuration error: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        }), 500

@app.route('/api/history', methods=['GET'])
def list_history():
    """List recent application history, newest first."""
    try:
        limit = request.args.get('limit', default=50, type=int)
        applications = history_store.list_applications(limit=limit)
        return jsonify({'success': True, 'applications': applications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history/<int:application_id>', methods=['GET'])
def get_history_item(application_id):
    """Get full details (including stored job analysis) for one past application."""
    try:
        application = history_store.get_application(application_id)
        if application is None:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        return jsonify({'success': True, 'application': application})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/history/<int:application_id>', methods=['DELETE'])
def delete_history_item(application_id):
    """Delete a past application record."""
    try:
        deleted = history_store.delete_application(application_id)
        if not deleted:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download generated files."""
    try:
        # Security: only allow files from output directory
        if not filename.startswith('output/'):
            return jsonify({'error': 'Invalid file path'}), 403
        
        file_path = filename
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize components on startup
    try:
        initialize_components()
        print("✅ All components initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize components: {e}")
        print("💡 Make sure DEEPSEEK_API_KEY is set in .env file")
    
    print("\n🚀 Starting Flask web server...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
