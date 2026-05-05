from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Configure logging instead of print statements
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory store (demo only - NOT for production)
notes = []

# ========================
# Secure API Endpoints
# ========================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for orchestration"""
    return jsonify({'status': 'ok', 'service': 'devsecops-app'}), 200


@app.route('/login', methods=['POST'])
def login():
    """
    Login endpoint - demonstrates secure authentication principles
    SECURITY: Uses parameterized/structured validation
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    # SECURITY: Avoid logging sensitive data
    logger.info(f"Login attempt for user: {username}")

    # In real app: hash passwords with bcrypt, query secure database
    # This is a DEMO - do NOT use hardcoded credentials in production
    if username == 'admin' and password == 'password':
        # SECURITY: Return minimal token, should be JWT in production
        return jsonify({'token': 'demo-token-123'}), 200

    logger.warning(f"Failed login for user: {username}")
    return jsonify({'error': 'invalid credentials'}), 401


@app.route('/notes', methods=['GET', 'POST'])
def notes_route():
    """
    Notes API - demonstrates input validation
    SECURITY: Validates input, avoids injection attacks
    """
    if request.method == 'POST':
        data = request.get_json() or {}
        note = data.get('note', '').strip()

        # Input validation: prevent empty notes
        if not note:
            return jsonify({'error': 'note cannot be empty'}), 400

        # Input validation: limit length to prevent abuse
        if len(note) > 1000:
            return jsonify({'error': 'note too long (max 1000 chars)'}), 400

        logger.info(f"Note added: {len(note)} characters")
        notes.append({'id': len(notes) + 1, 'content': note})

        return jsonify({'message': 'note added', 'total': len(notes)}), 201

    # GET: Return all notes
    logger.info(f"Returning {len(notes)} notes")
    return jsonify({'notes': notes, 'total': len(notes)}), 200


@app.route('/api/version', methods=['GET'])
def version():
    """Return application version"""
    return jsonify({'version': '1.0.0', 'environment': 'production'}), 200


# ========================
# Error Handling
# ========================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 - prevents information disclosure"""
    return jsonify({'error': 'not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 - generic message, log details"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'internal server error'}), 500


# ========================
# Main
# ========================

if __name__ == '__main__':
    # SECURITY: Bind only to localhost in dev, override with env in prod
    # SECURITY: Debug mode MUST be False in production
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False,  # Never debug=True in production
        use_reloader=False  # Disable reloader in containerized environments
    )
