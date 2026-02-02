"""
ANTIGRAVITY TAILOR - Strategic Analyzer
Implementa o Proactive Protocol do Thiago
"""

from typing import List, Tuple
from core.models import Job, Seniority, StrategicPlan

BIG_CORPS = ["meta", "facebook", "google", "ambev", "abinbev", "suzano", "dow", "transperfect", "nubank", "ifood"]

class StrategicAnalyzer:
    def __init__(self, debug: bool = False):
        self.debug = debug

    def analyze(self, job: Job) -> StrategicPlan:
        """
        Gera o Plano Estratégico baseado na vaga e no perfil do Thiago
        """
        ghost_notes = self._identify_ghost_notes(job)
        vulnerabilities = self._analyze_vulnerabilities(job)
        anti_overqual, shift = self._anti_overqualification_protocol(job)
        
        return StrategicPlan(
            ghost_notes=ghost_notes,
            vulnerability_report=vulnerabilities,
            anti_overqualification_applied=anti_overqual,
            suggested_narrative_shift=shift,
            approved=False
        )

    def _identify_ghost_notes(self, job: Job) -> List[str]:
        """Identifica necessidades implícitas (Ghost Notes)"""
        notes = []
        
        # Heurísticas por tipo de vaga
        if job.job_type == "marketing":
            notes.append("Implicitamente precisa de Gestão de Stakeholders e Alinhamento com Vendas (Sales Enablement).")
            notes.append("Provável necessidade de justificativa de ROI agressiva para o boardroom.")
        
        if job.job_type == "growth":
            notes.append("Ghost Note: Foco extremo em CAC/LTV e experimentação rápida, possivelmente sem infraestrutura pronta.")
            notes.append("Precisará 'sujar as mãos' com dados antes de automatizar.")
            
        if job.job_type == "ai":
            notes.append("Expectativa mágica sobre IA: Precisa vender 'eficiência operacional' mais do que 'tecnologia'.")
            
        if "lead" in job.title.lower() or "gerente" in job.title.lower():
            notes.append("Precisa de alguém que resolva conflitos de time sem escalar para o VP.")
            
        return notes

    def _analyze_vulnerabilities(self, job: Job) -> List[str]:
        """Onde o Thiago corre risco de parecer caro ou sênior demais?"""
        report = []
        
        # Risco por Senioridade / USP
        if "Mestrado USP" in job.description: # Heurística se ele pesquisou
            report.append("RISCO: Perfil acadêmico (USP) pode parecer 'teórico demais' para esta vaga.")
        
        # Risco por Big Corp
        is_big_org = any(org in job.company.lower() for org in BIG_CORPS)
        if not is_big_org and job.seniority in [Seniority.LEAD, Seniority.MANAGER]:
            report.append(f"RISCO: Sua experiência em {job.company} pode parecer 'corporativa demais' para uma empresa menor.")
            report.append("DICA: Enfatizar agilidade e execução hands-on (menos processos, mais resultados).")
            
        # Risco Salarial
        if job.seniority == Seniority.JUNIOR:
            report.append("CRÍTICO: Perfil 15+ anos é 100% overqualified aqui. Requer downgrade total de títulos.")
            
        return report

    def _anti_overqualification_protocol(self, job: Job) -> Tuple[bool, str]:
        """Aplica a regra de Anti-overqualification"""
        is_big_corp = any(org in job.company.lower() for org in BIG_CORPS)
        
        if not is_big_corp:
            # Para empresas menores, enfatizar Lead Hands-on e ocultar Head
            return True, "Narrativa: 'Lead Hands-on'. Ocultar títulos de 'Head' e 'Gerente Sênior' para não assustar o budget."
        
        return False, "Narrativa: 'Strategic Leader'. Manter títulos originais e focar em impacto de P&L de grande escala."
