#!/usr/bin/env python3
"""
Webhook Server para integração com n8n
Recebe POST com descrição da vaga, retorna PDF
"""

from flask import Flask, request, send_file, jsonify
from pipeline import generate_resume
import tempfile
import os

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    """
    POST /generate
    Body: {"job_description": "...", "output_name": "optional"}
    Returns: PDF file
    """
    data = request.json or {}
    job_text = data.get('job_description', '')
    output_name = data.get('output_name')
    
    if not job_text:
        return jsonify({"error": "job_description required"}), 400
    
    try:
        # Salva texto temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(job_text)
            temp_path = f.name
        
        # Gera PDF
        pdf_path = generate_resume(temp_path, output_name)
        
        # Limpa temp
        os.unlink(temp_path)
        
        # Retorna PDF
        if pdf_path.endswith('.pdf') and os.path.exists(pdf_path):
            return send_file(pdf_path, mimetype='application/pdf')
        else:
            return jsonify({"html_path": pdf_path}), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "taylor-resume-pipeline"})


if __name__ == '__main__':
    print("🚀 Webhook Server rodando em http://localhost:5555")
    app.run(host='0.0.0.0', port=5555, debug=False)
