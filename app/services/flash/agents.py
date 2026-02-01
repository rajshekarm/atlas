"""
Main Agents Module
Orchestrates different AI agents for the Flash service
"""
from app.services.flash.agents.resume_agent import ResumeAgent
from app.services.flash.agents.qa_agent import QAAgent

__all__ = ['ResumeAgent', 'QAAgent']
