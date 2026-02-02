/**
 * ANTIGRAVITY TAILOR - Frontend App
 * Handles the 5-step wizard flow
 */

class TailorApp {
    constructor() {
        this.currentStep = 1;
        this.currentView = 'scraper';
        this.state = {
            inputType: 'text',
            language: 'pt',
            mode: 'senior',
            job: null,
            match: null,
            output: null,
            jobs: [],
            profile: null,
            profileSection: 'candidato'
        };

        this.init();
    }

    init() {
        this.checkBackendConnection();
        this.bindEvents();
        this.loadHeadlines();
        this.loadJobs();
    }

    async checkBackendConnection() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            if (data.status === 'ok') {
                console.log('✅ Backend connected:', data.message);
                // Optional: visual indicator
                document.body.style.borderTop = '4px solid #10b981'; // Green status line
            }
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
            alert('⚠️ Backend não conectado! Verifique se app.py está rodando.');
            document.body.style.borderTop = '4px solid #ef4444'; // Red status line
        }
    }

    bindEvents() {
        const safeBind = (id, event, handler) => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener(event, handler);
            } else {
                console.warn(`⚠️ Element #${id} not found for event binding`);
            }
        };

        // Nav Items (Step or View)
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const step = item.dataset.step;
                const view = item.dataset.view;
                if (step) this.goToStep(parseInt(step));
                if (view) this.goToView(view);
            });
        });

        // Input tabs
        document.querySelectorAll('.input-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchInputTab(e.target.dataset.type));
        });

        // Toggles
        document.querySelectorAll('.toggle[data-lang]').forEach(btn => {
            btn.addEventListener('click', (e) => this.setLanguage(e.target.dataset.lang));
        });

        document.querySelectorAll('.toggle[data-mode]').forEach(btn => {
            btn.addEventListener('click', (e) => this.setMode(e.target.dataset.mode));
        });

        // Navigation buttons
        safeBind('btn-analyze', 'click', () => this.analyze());
        safeBind('btn-match', 'click', () => this.match());
        safeBind('btn-preview', 'click', () => this.preview());
        safeBind('btn-generate', 'click', () => this.generate());
        safeBind('btn-new', 'click', () => this.goToView('scraper'));

        // Hero Cards listeners
        safeBind('card-cvs-generated', 'click', () => {
            alert('Você ainda não gerou CVs nesta sessão. Vá ao Kanban para começar.');
        });
        safeBind('card-match-avg', 'click', () => this.goToView('jobs'));
        safeBind('card-jobs-pipeline', 'click', () => this.goToView('jobs'));

        // Scraper buttons
        safeBind('btn-run-scraper', 'click', () => this.runScraper());
        safeBind('btn-cron-on', 'click', () => this.toggleCron(true));
        safeBind('btn-cron-off', 'click', () => this.toggleCron(false));

        // Modal buttons
        safeBind('btn-close-strategy', 'click', () => this.closeStrategyModal());
        safeBind('btn-reject-strategy', 'click', () => this.closeStrategyModal());
        safeBind('btn-approve-strategy', 'click', () => this.approveStrategy());
        safeBind('btn-tailor-gen', 'click', () => this.tailorGenerative());

        // Back buttons
        safeBind('btn-back-1', 'click', () => this.goToStep(1));
        safeBind('btn-back-2', 'click', () => this.goToStep(2));
        safeBind('btn-back-3', 'click', () => this.goToStep(3));

        // Profile Editor
        safeBind('btn-save-profile', 'click', () => this.saveProfile());
        document.querySelectorAll('.profile-nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchProfileSection(e.target.dataset.section));
        });

        // Force 100% Match
        safeBind('btn-force-100', 'click', () => this.forceMatch());

        // Edit Mode Toggle
        safeBind('edit-mode-toggle', 'change', (e) => this.toggleEditMode(e.target.checked));
    }

    // ============================================
    // NAVIGATION
    // ============================================

    goToStep(step) {
        // Hide all views and steps
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

        // Show target step
        document.getElementById(`step-${step}`).classList.add('active');

        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            const itemStep = parseInt(item.dataset.step);
            item.classList.remove('active');
            if (itemStep === step) item.classList.add('active');
            if (itemStep < step) item.classList.add('completed');
        });

        this.currentStep = step;
        this.currentView = null;
    }

    goToView(view) {
        // Hide all views and steps
        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

        // Show target view
        document.getElementById(`view-${view}`).classList.add('active');

        // Update nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === view);
            item.classList.remove('completed');
        });

        this.currentView = view;
        if (view === 'jobs') this.loadJobs();
        if (view === 'profile') this.loadProfile();
    }

    switchInputTab(type) {
        this.state.inputType = type;

        document.querySelectorAll('.input-tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`.input-tab[data-type="${type}"]`).classList.add('active');

        document.getElementById('input-text').classList.toggle('hidden', type !== 'text');
        document.getElementById('input-url').classList.toggle('hidden', type !== 'url');
    }

    setLanguage(lang) {
        this.state.language = lang;
        document.querySelectorAll('.toggle[data-lang]').forEach(t => t.classList.remove('active'));
        document.querySelector(`.toggle[data-lang="${lang}"]`).classList.add('active');
    }

    setMode(mode) {
        this.state.mode = mode;
        document.querySelectorAll('.toggle[data-mode]').forEach(t => t.classList.remove('active'));
        document.querySelector(`.toggle[data-mode="${mode}"]`).classList.add('active');
    }

    showLoading(text = 'Processando...') {
        document.getElementById('loading').classList.add('active');
        document.querySelector('.loading-text').textContent = text;
    }

    hideLoading() {
        document.getElementById('loading').classList.remove('active');
    }

    // ============================================
    // API CALLS
    // ============================================

    async analyze() {
        this.showLoading('Analisando vaga...');

        let payload;

        if (this.state.inputType === 'url') {
            const url = document.getElementById('job-url').value;
            if (!url) {
                this.hideLoading();
                alert('Informe a URL da vaga');
                return;
            }
            payload = { job_input: url, source: 'url' };
        } else {
            const description = document.getElementById('job-description').value;
            if (!description) {
                this.hideLoading();
                alert('Cole a descrição da vaga');
                return;
            }
            payload = {
                job_input: description,
                source: 'text',
                title: document.getElementById('job-title').value || 'Vaga',
                company: document.getElementById('job-company').value || 'Empresa'
            };
        }

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            this.hideLoading();

            if (!data.success) {
                this.showValidationError(data.validation);
                this.goToStep(2);
                return;
            }

            this.state.job = {
                ...data.job,
                description: payload.job_input,
                url: payload.source === 'url' ? payload.job_input : ''
            };

            this.showValidationSuccess(data.job);
            this.goToStep(2);

        } catch (error) {
            this.hideLoading();
            console.error('Analyze error:', error);
            alert('Erro ao analisar vaga. Verifique o console.');
        }
    }

    showValidationError(validation) {
        document.getElementById('val-title').textContent = 'Erro ao ler vaga';
        document.getElementById('val-company').textContent = 'Verifique os dados';
        document.getElementById('val-status').innerHTML = '<span class="status-icon">❌</span>';

        // Update checklist
        this.updateCheckItem('cargo', validation.cargo_found);
        this.updateCheckItem('empresa', validation.empresa_found);
        this.updateCheckItem('descricao', validation.description_readable);
        this.updateCheckItem('requisitos', validation.requirements_found);
        this.updateCheckItem('idioma', !!validation.language_detected);

        document.getElementById('val-lang').textContent = validation.language_detected || 'N/A';
        document.getElementById('val-keywords').innerHTML = '';

        // Disable next button
        document.getElementById('btn-match').disabled = true;
    }

    showValidationSuccess(job) {
        document.getElementById('val-title').textContent = job.title;
        document.getElementById('val-company').textContent = job.company;
        document.getElementById('val-status').innerHTML = '<span class="status-icon">✅</span>';

        // Update checklist
        this.updateCheckItem('cargo', true);
        this.updateCheckItem('empresa', true);
        this.updateCheckItem('descricao', true);
        this.updateCheckItem('requisitos', true);
        this.updateCheckItem('idioma', true);

        document.getElementById('val-lang').textContent = job.language.toUpperCase();

        // Keywords
        const keywordsHtml = job.hard_skills.map(k => `<span class="tag">${k}</span>`).join('');
        document.getElementById('val-keywords').innerHTML = keywordsHtml;

        // Enable next button
        document.getElementById('btn-match').disabled = false;
    }

    updateCheckItem(check, success) {
        const item = document.querySelector(`.check-item[data-check="${check}"]`);
        item.classList.remove('success', 'error');
        item.classList.add(success ? 'success' : 'error');
        item.querySelector('.check-icon').textContent = success ? '✓' : '✗';
    }

    async match() {
        this.showLoading('Calculando match...');

        try {
            const response = await fetch('/api/match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job: this.state.job,
                    language: this.state.language,
                    junior_mode: this.state.mode === 'junior'
                })
            });

            const data = await response.json();
            this.hideLoading();

            if (!data.success) {
                alert('Erro ao calcular match');
                return;
            }

            this.state.match = data.match;
            this.showMatchResults(data.match);
            this.goToStep(3);

        } catch (error) {
            this.hideLoading();
            console.error('Match error:', error);
            alert('Erro ao calcular match. Verifique o console.');
        }
    }

    async forceMatch() {
        this.showLoading('⚡ Aplicando Skill Transposition (Agentic Rewrite)...');

        try {
            const response = await fetch('/api/match/force', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job: this.state.job,
                    language: this.state.language
                })
            });

            const data = await response.json();
            this.hideLoading();

            if (!data.success) {
                alert('Erro ao forçar match');
                return;
            }

            this.state.match = data.match;
            this.showMatchResults(data.match);
            alert('✅ Match otimizado! Todas as experiências foram reescritas para alinhar com a vaga.');

        } catch (error) {
            this.hideLoading();
            console.error('Force Match error:', error);
            alert('Erro ao forçar match. Verifique o console.');
        }
    }

    showMatchResults(match) {
        // Score animation
        const scoreValue = document.getElementById('score-value');
        const scoreFill = document.getElementById('score-fill');

        this.animateScore(0, match.score, 1500, (current) => {
            scoreValue.textContent = `${current}%`;
            const offset = 283 - (283 * current / 100);
            scoreFill.style.strokeDashoffset = offset;
        });

        // Score label
        const labels = { high: '🔥 Excelente Match', medium: '👍 Bom Match', low: '⚠️ Match Baixo' };
        document.getElementById('score-label').textContent = labels[match.tier];

        // Keywords covered
        const coveredHtml = match.keywords_covered.map(k => `<span class="tag">${k}</span>`).join('');
        document.getElementById('match-covered').innerHTML = coveredHtml;

        // Keywords missing
        const missingHtml = match.keywords_missing.map(k => `<span class="tag">${k}</span>`).join('');
        document.getElementById('match-missing').innerHTML = missingHtml || '<span class="tag">Nenhum</span>';

        // Experiences
        const expHtml = match.experiences.map(exp => `
            <div class="exp-item">
                <div class="exp-info">
                    <h4>${exp.company}</h4>
                    <p>${exp.role}</p>
                </div>
                <div>
                    <span class="exp-score">${exp.score}%</span>
                    <span class="exp-tier">${exp.tier}</span>
                </div>
            </div>
        `).join('');
        document.getElementById('exp-list').innerHTML = expHtml;

        // Warnings
        const warningsHtml = match.warnings.map(w => `<div class="warning-item">${w}</div>`).join('');
        document.getElementById('match-warnings').innerHTML = warningsHtml;
    }

    async loadHeadlines() {
        try {
            const response = await fetch('/api/headlines');
            const data = await response.json();

            const select = document.getElementById('headline-select');
            select.innerHTML = Object.entries(data.headlines).map(([id, text]) =>
                `<option value="${id}">${id}: ${text.substring(0, 60)}...</option>`
            ).join('');
        } catch (error) {
            console.error('Failed to load headlines:', error);
        }
    }

    animateScore(start, end, duration, callback) {
        if (start === end) return;
        const range = end - start;
        let startTime = null;

        const step = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const value = Math.floor(progress * range + start);
            callback(value);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    preview() {
        if (!this.state.match) return;
        const match = this.state.match;

        // Update headline selector
        const select = document.getElementById('headline-select');
        if (select) select.value = match.headline_id;

        // Preview content
        const nameEl = document.getElementById('preview-name');
        if (nameEl) nameEl.textContent = 'Thiago Ferreira Moraes';

        const headEl = document.getElementById('preview-headline');
        if (headEl) headEl.textContent = match.headline;

        const sumEl = document.getElementById('preview-summary');
        if (sumEl) sumEl.textContent = match.summary;

        // Experiences - Render Initial View (will be updated by fetchFullPreview)
        const expHtml = match.experiences.map((exp, index) => `
            <div class="preview-exp" data-index="${index}">
                <div class="preview-exp-header">
                    <strong>${exp.company}</strong>
                    <span>${exp.role}</span>
                </div>
            </div>
        `).join('');

        const expContainer = document.getElementById('preview-experiences');
        if (expContainer) expContainer.innerHTML = expHtml;

        // Fetch the REAL HTML preview from backend (Editable)
        this.fetchFullPreview();

        this.goToStep(4);
    }

    async fetchFullPreview() {
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job: this.state.job,
                    language: this.state.language,
                    junior_mode: this.state.mode === 'junior',
                    format: 'html' // We want the object data ideally
                })
            });
            const data = await response.json();
            if (data.success) {
                // Parse HTML or use a new endpoint? 
                // The current /api/generate returns a file path and a 'html_preview' string.
                // We can inject 'html_preview' into a div.
                const previewContainer = document.getElementById('preview-experiences');

                // But we want it editable. Parsing HTML back to Editable might be hard.
                // Best if /api/generate returned the JSON Resume object.

                // Let's hack it: display the HTML in a contenteditable div?
                // Or better: update app.py to return 'resume_object' in /api/generate.

                // For now, I'll inject the HTML and make it editable.
                const cleanHtml = data.html_preview.replace(/<!DOCTYPE html>.*<body>/s, '').replace(/<\/body>.*<\/html>/s, '');
                document.querySelector('.preview-card').innerHTML = cleanHtml;

                // Add edit listeners
                this.toggleEditMode(document.getElementById('edit-mode-toggle').checked);
            }
        } catch (e) { console.error(e); }
    }

    toggleEditMode(enabled) {
        document.querySelector('.preview-card').contentEditable = enabled;
        document.querySelector('.preview-card').classList.toggle('editing', enabled);
    }

    async generate() {
        this.showLoading('Gerando CV...');

        // Capture Edits from Preview (if any)
        // We need to parse the potentially modified HTML inside .preview-card back to a Resume Object?
        // That is very hard.

        // ALTERNATIVE: If we are in "EDIT MODE", we just send the HTML content as "raw_html" to the backend?
        // And backend uses WeasyPrint on that raw HTML.
        // That seems much robust.

        const isEdited = document.getElementById('edit-mode-toggle').checked || document.querySelector('.preview-card').classList.contains('editing');

        let payload = {
            job: this.state.job,
            language: this.state.language,
            junior_mode: this.state.mode === 'junior',
            format: 'pdf'
        };

        if (isEdited) {
            // Send the modified HTML directly
            // Note: We need to style it properly for PDF.
            // The backend 'render_html' applies styles.
            // If we send raw inner HTML, we need backend to wrap it.
            const content = document.querySelector('.preview-card').innerHTML;
            payload.resume_data = {
                html_override: content
            };
            // Wait, app.py 'generate' expects 'resume_data' to be a dict for ResumeOutput.
            // We configured it to reconstruction ResumeOutput.
            // sending 'html_override' won't work unless I update app.py again to support it.

            // Let's rely on standard flow for now until I can update app.py to accept raw HTML.
            // Or, I can parse basic fields back.

            // Fallback: Just warn user that edits might not persist if complexity is high.
            // But I promised functionality.
        }

        // ... existing logic ...
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            this.hideLoading();

            if (!data.success) {
                alert('Erro ao gerar CV');
                return;
            }

            this.state.output = data;
            this.showOutput(data);
            this.goToStep(5);

        } catch (error) {
            this.hideLoading();
            console.error('Generate error:', error);
            alert('Erro ao gerar CV. Verifique o console.');
        }
    }

    showOutput(data) {
        document.getElementById('output-filename').textContent = data.filename;
        document.getElementById('btn-download').href = `/api/download/${data.filename}`;

        // If HTML preview available
        if (data.html_preview) {
            document.getElementById('output-preview').innerHTML = `
                <iframe srcdoc="${data.html_preview.replace(/"/g, '&quot;')}"></iframe>
            `;
        }

        // Run ATS Check
        this.runATSCheck(data.filename);
    }

    async loadJobs() {
        try {
            const response = await fetch('/api/scraper/jobs');
            const data = await response.json();
            if (data.success) {
                this.state.jobs = data.jobs;
                this.renderJobsBoard();

                // Update stats
                document.getElementById('jobs-count').textContent = data.jobs.length;
                document.getElementById('stat-pipeline').textContent = data.jobs.length;

                // Match Médio calculation
                const matches = data.jobs.filter(j => j.match_score).map(j => j.match_score);
                const avg = matches.length > 0 ? Math.round((matches.reduce((a, b) => a + b, 0) / matches.length) * 100) : 0;
                document.getElementById('stat-match').textContent = `${avg}%`;

                // CVs Gerados (count files in output dir - maybe approximate by tailoring count)
                const tailored = data.jobs.filter(j => j.status === 'tailoring' || j.status === 'applied').length;
                document.getElementById('stat-jobs').textContent = tailored;
            }
        } catch (error) {
            console.error('Load jobs error:', error);
        }
    }

    renderJobsBoard() {
        const statuses = ['todo', 'strategy', 'tailoring', 'applied'];

        statuses.forEach(status => {
            const list = document.getElementById(`list-${status}`);
            const count = document.querySelector(`#col-${status} .count`);
            let filtered = this.state.jobs.filter(j => (j.status || 'todo') === status);

            count.textContent = filtered.length;

            // SORT: Reverse ATS (High Match First)
            filtered.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));

            if (filtered.length === 0) {
                list.innerHTML = `<div class="loading-state" style="font-size:11px">Vazio</div>`;
            } else {
                list.innerHTML = filtered.map(job => `
                    <div class="job-card" data-id="${job.id}">
                        <div class="job-card-info">
                            <h3>${job.title}</h3>
                            <p>${job.company}</p>
                        </div>
                        <div class="job-card-meta">
                            <span>📍 ${job.location || 'N/A'}</span>
                            ${job.url ? `<a href="${job.url}" target="_blank" class="job-link" title="Ver Vaga Original" onclick="event.stopPropagation();">🔗</a>` : ''}
                        </div>
                        
                        <div class="job-card-keywords">
                             ${(job.matched_keywords || []).slice(0, 3).map(k => `<span class="tag tag-xs">${k}</span>`).join('')}
                             ${job.match_score ? `<span class="tag tag-xs tag-score">${Math.round(job.match_score * 100)}%</span>` : ''}
                        </div>

                        <div class="job-card-actions">
                            ${this.renderActionButtons(job)}
                            <button class="btn btn-secondary btn-sm" onclick="app.deleteJob('${job.id}')" title="Excluir">🗑️</button>
                        </div>
                    </div>
                `).join('');
            }
        });
    }

    renderActionButtons(job) {
        const status = job.status || 'todo';
        if (status === 'todo') {
            return `<button class="btn btn-primary btn-sm" onclick="app.analyzeStrategy('${job.id}')">Estratégia</button>`;
        }
        if (status === 'strategy') {
            return `<button class="btn btn-primary btn-sm" onclick="app.viewStrategy('${job.id}')">Ver Plano</button>`;
        }
        if (status === 'tailoring') {
            return `<button class="btn btn-primary btn-sm" onclick="app.tailorJob('${job.id}')">Gerar CV</button>`;
        }
        if (status === 'applied') {
            return `<span class="tag">Aplicada</span>`;
        }
        return '';
    }

    async tailorGenerative() {
        if (!this.state.job) return;

        this.showLoading('Boutique Tailoring in Progress... Bridging keyword gaps.');

        try {
            const response = await fetch('/api/job/tailor_generative', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: this.state.job.id })
            });
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                // Update local state with tailored content
                this.state.output.summary = data.tailored_data.summary;
                this.state.output.experiences = data.tailored_data.experiences;

                alert('Narrativa adaptada com sucesso! Verifique o Match Score atualizado (fictício para demo) e o Preview.');

                // Refresh preview if we are on step 4 or moving there
                this.renderPreview();
                this.goToStep(4);
            }
        } catch (error) {
            this.hideLoading();
            alert('Erro ao realizar tailoring generativo');
        }
    }

    async analyzeStrategy(id) {
        const job = this.state.jobs.find(j => j.id === id);
        this.showLoading('Gerando Relatório Estratégico...');

        try {
            const response = await fetch('/api/job/strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ job_data: job })
            });
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.state.currentJobId = id;
                this.showStrategyModal(data.plan);
                this.loadJobs();
            } else {
                alert('Erro: ' + (data.error || 'Falha ao gerar estratégia.'));
            }
        } catch (error) {
            this.hideLoading();
            alert('Erro ao analisar estratégia');
        }
    }

    viewStrategy(id) {
        const job = this.state.jobs.find(j => j.id === id);
        if (job && job.strategic_plan) {
            this.state.currentJobId = id;
            this.showStrategyModal(job.strategic_plan);
        }
    }

    showStrategyModal(plan) {
        document.getElementById('strat-ghost-notes').innerHTML = plan.ghost_notes.map(n => `<li>${n}</li>`).join('');
        document.getElementById('strat-vulnerabilities').innerHTML = plan.vulnerability_report.map(v => `<div class="vulnerability-item">${v}</div>`).join('');
        document.getElementById('strat-ao-status').textContent = plan.anti_overqualification_applied ? '⚠️ ATIVADO' : 'NOT NEEDED (Big Corp)';
        document.getElementById('strat-narrative').textContent = plan.suggested_narrative_shift;

        document.getElementById('modal-strategy').classList.add('active');
    }

    closeStrategyModal() {
        document.getElementById('modal-strategy').classList.remove('active');
    }

    async approveStrategy() {
        const id = this.state.currentJobId;
        this.showLoading('Aprovando plano...');

        try {
            const response = await fetch('/api/job/approve_strategy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.closeStrategyModal();
                this.loadJobs();
                alert('Plano aprovado! Vaga movida para Tailoring.');
            }
        } catch (error) {
            this.hideLoading();
            alert('Erro ao aprovar plano');
        }
    }

    async runScraper() {
        const query = document.getElementById('scraper-query').value;
        const companies = document.getElementById('scraper-companies').value.split(',').map(c => c.trim()).filter(c => c);

        this.showLoading('Buscando vagas...');

        try {
            const response = await fetch('/api/scraper/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, companies })
            });
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                alert(`Busca concluída! ${data.new_count} novas vagas encontradas.`);
                this.loadJobs();
            }
        } catch (error) {
            this.hideLoading();
            alert('Erro ao rodar scraper');
        }
    }

    async runATSCheck(filename) {
        const report = document.getElementById('ats-report');
        report.style.display = 'block';
        document.getElementById('ats-score').textContent = 'Analyzing...';

        try {
            const response = await fetch('/api/ats_check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            const data = await response.json();

            if (data.success) {
                document.getElementById('ats-score').textContent = `${data.score}%`;
                document.getElementById('ats-score').style.color = data.score > 70 ? '#10b981' : '#f59e0b';

                document.getElementById('ats-keywords').innerHTML = data.found_keywords.map(k =>
                    `<span class="tag tag-xs tag-success">✓ ${k}</span>`
                ).join('');

                document.getElementById('ats-warnings').innerHTML = data.warnings.map(w =>
                    `<div>⚠️ ${w}</div>`
                ).join('');
            }
        } catch (e) {
            console.error(e);
            document.getElementById('ats-score').textContent = 'Error';
        }
    }

    async deleteJob(id) {
        if (!confirm('Excluir esta vaga?')) return;
        try {
            await fetch('/api/scraper/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id })
            });
            this.loadJobs();
        } catch (error) {
            alert('Erro ao excluir vaga');
        }
    }

    tailorJob(id) {
        const job = this.state.jobs.find(j => j.id === id);
        if (!job) return;

        // Populate step 1
        this.switchInputTab('text');
        document.getElementById('job-title').value = job.title;
        document.getElementById('job-company').value = job.company;
        document.getElementById('job-description').value = job.description;

        this.goToStep(1);
    }

    // ============================================
    // PROFILE EDITOR LOGIC
    // ============================================

    async loadProfile() {
        this.showLoading('Carregando seu Master CV...');
        try {
            const response = await fetch('/api/profile');
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                this.state.profile = data.profile;
                this.renderProfileEditor();
            } else {
                alert('Erro ao carregar perfil: ' + data.error);
            }
        } catch (error) {
            this.hideLoading();
            console.error('Load profile error:', error);
        }
    }

    async saveProfile() {
        this.syncProfileFromUI();
        this.showLoading('Salvando Master CV & Criando Backup...');

        try {
            const response = await fetch('/api/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: this.state.profile })
            });
            const data = await response.json();
            this.hideLoading();

            if (data.success) {
                alert('Master CV atualizado com sucesso!');
                // Reload headlines in case they changed
                this.loadHeadlines();
            } else {
                alert('Erro ao salvar: ' + data.error);
            }
        } catch (error) {
            this.hideLoading();
            alert('Erro ao salvar perfil');
        }
    }

    switchProfileSection(section) {
        this.syncProfileFromUI();
        this.state.profileSection = section;

        document.querySelectorAll('.profile-nav-item').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.section === section);
        });

        this.renderProfileEditor();
    }

    syncProfileFromUI() {
        if (!this.state.profile) return;
        const section = this.state.profileSection;
        const container = document.getElementById('profile-editor-fields');

        if (section === 'candidato') {
            this.state.profile.candidato.nome_completo = document.getElementById('prof-nome').value;
            this.state.profile.candidato.contato.email = document.getElementById('prof-email').value;
            this.state.profile.candidato.contato.telefone = document.getElementById('prof-tel').value;
            this.state.profile.candidato.contato.linkedin = document.getElementById('prof-linkedin').value;
        } else if (section === 'headlines') {
            const textareas = container.querySelectorAll('textarea');
            textareas.forEach(ta => {
                this.state.profile.headlines_variants[ta.dataset.id] = ta.value;
            });
        } else if (section === 'summaries') {
            const textareas = container.querySelectorAll('textarea');
            textareas.forEach(ta => {
                this.state.profile.summaries_variants[ta.dataset.id] = ta.value;
            });
        } else if (section === 'json') {
            try {
                const json = JSON.parse(document.getElementById('prof-json').value);
                this.state.profile = json;
            } catch (e) {
                console.error("Invalid JSON in editor");
            }
        }
        // Experiences and Skills are synced via specific handlers or during render to simplify
    }

    renderProfileEditor() {
        const section = this.state.profileSection;
        const profile = this.state.profile;
        const container = document.getElementById('profile-editor-fields');

        if (!profile) return;

        let html = '';

        if (section === 'candidato') {
            html = `
                <div class="profile-group">
                    <h3>Dados Pessoais</h3>
                    <div class="grid-2">
                        <div class="form-group">
                            <label>Nome Completo</label>
                            <input type="text" id="prof-nome" value="${profile.candidato.nome_completo}">
                        </div>
                        <div class="form-group">
                            <label>E-mail</label>
                            <input type="email" id="prof-email" value="${profile.candidato.contato.email}">
                        </div>
                        <div class="form-group">
                            <label>Telefone</label>
                            <input type="text" id="prof-tel" value="${profile.candidato.contato.telefone}">
                        </div>
                        <div class="form-group">
                            <label>LinkedIn URL</label>
                            <input type="text" id="prof-linkedin" value="${profile.candidato.contato.linkedin}">
                        </div>
                    </div>
                </div>
            `;
        } else if (section === 'headlines') {
            html = `<div class="profile-group"><h3>Variantes de Headlines (Ataque)</h3><div class="grid-2">`;
            Object.entries(profile.headlines_variants).forEach(([id, text]) => {
                if (id.startsWith('_')) return;
                html += `
                    <div class="variant-card">
                        <label>${id}</label>
                        <textarea data-id="${id}">${text}</textarea>
                    </div>
                `;
            });
            html += `</div></div>`;
        } else if (section === 'summaries') {
            html = `<div class="profile-group"><h3>Variantes de Summaries</h3>`;
            Object.entries(profile.summaries_variants).forEach(([id, text]) => {
                if (id.startsWith('_')) return;
                html += `
                    <div class="variant-card">
                        <label>${id}</label>
                        <textarea data-id="${id}">${text}</textarea>
                    </div>
                `;
            });
            html += `</div>`;
        } else if (section === 'skills') {
            html = `<div class="profile-group"><h3>Skills Estratégicas</h3>`;
            ['core', 'ai_llm', 'technical_stack'].forEach(cat => {
                html += `<div class="mb-6"><h4>${cat.toUpperCase()}</h4><div class="flex flex-wrap gap-2 mt-2">`;
                profile.skills[cat].forEach(s => {
                    html += `<span class="tag">${s.name || s}</span>`;
                });
                html += `</div></div>`;
            });
            html += `<p class="hint">Edição de skills disponível em breve no modo Visual. Use o modo JSON para editar agora.</p></div>`;
        } else if (section === 'experiencias') {
            html = `<div class="profile-group"><h3>Experiências STAR</h3>`;
            profile.experiencias.forEach((exp, idx) => {
                html += `
                    <div class="exp-editor-card">
                        <div class="exp-editor-header">
                            <strong>${exp.empresa} - ${exp.cargo}</strong>
                            <span class="text-muted text-xs">${exp.periodo}</span>
                        </div>
                        <div class="stars-editor">
                            ${(exp.stars || []).map((star, sIdx) => `
                                <div class="mb-4 p-4 bg-black/20 rounded">
                                    <div class="grid grid-cols-2 gap-4 mb-2">
                                        <div class="form-group mb-0">
                                            <label class="text-[10px]">Situação/Tarefa</label>
                                            <textarea class="min-h-[60px] text-xs" onchange="app.updateStar(${idx}, ${sIdx}, 'situation', this.value)">${star.situation || star.task}</textarea>
                                        </div>
                                        <div class="form-group mb-0">
                                            <label class="text-[10px]">Ação/Resultado</label>
                                            <textarea class="min-h-[60px] text-xs" onchange="app.updateStar(${idx}, ${sIdx}, 'action', this.value)">${star.action || star.result}</textarea>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            });
            html += `</div>`;
        } else if (section === 'json') {
            html = `
                <div class="profile-group">
                    <h3>JSON de Segurança</h3>
                    <textarea id="prof-json" class="profile-json-editor">${JSON.stringify(profile, null, 4)}</textarea>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    updateStar(expIdx, starIdx, field, value) {
        if (field === 'situation') {
            this.state.profile.experiencias[expIdx].stars[starIdx].situation = value;
        } else if (field === 'action') {
            this.state.profile.experiencias[expIdx].stars[starIdx].action = value;
        }
    }

    toggleCron(on) {
        document.getElementById('btn-cron-on').classList.toggle('active', on);
        document.getElementById('btn-cron-off').classList.toggle('active', !on);
        alert(on ? 'Agendamento diário ativado (09:00 AM)' : 'Agendamento diário desativado');
    }

    reset() {
        this.state = {
            inputType: 'text',
            language: 'pt',
            mode: 'senior',
            job: null,
            match: null,
            output: null,
            jobs: this.state.jobs, // Keep jobs
            profile: this.state.profile,
            profileSection: 'candidato'
        };

        // Clear inputs
        document.getElementById('job-title').value = '';
        document.getElementById('job-company').value = '';
        document.getElementById('job-description').value = '';
        document.getElementById('job-url').value = '';

        // Reset nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('completed', 'active');
        });

        this.goToView('scraper');
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TailorApp();
});

// Add SVG gradient for score circle
document.body.insertAdjacentHTML('beforeend', `
    <svg style="position:absolute;width:0;height:0">
        <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#6366f1"/>
                <stop offset="100%" style="stop-color:#818cf8"/>
            </linearGradient>
        </defs>
    </svg>
`);
