from crewai import Agent, Task, Crew
from crewai.agent import Agent
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
import yaml
import os
from typing import Dict, Any, List, Optional
import logging
from app.core.cost_tracker import cost_tracker, TokenUsage

logger = logging.getLogger(__name__)


class CostTrackingCallback(BaseCallbackHandler):
    """Callback handler to track token usage for cost estimation"""
    
    def __init__(self, agent_name: str, task_description: Optional[str] = None):
        self.agent_name = agent_name
        self.task_description = task_description
        self.token_usage = TokenUsage()
        
    def on_llm_end(self, response, **kwargs):
        """Called when an LLM call ends"""
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            if usage:
                self.token_usage.prompt_tokens += usage.get('prompt_tokens', 0)
                self.token_usage.completion_tokens += usage.get('completion_tokens', 0)
                self.token_usage.total_tokens += usage.get('total_tokens', 0)


class BaseCrew:
    """Base class for loading CrewAI configurations from YAML files"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "../config")
        
        self.config_dir = config_dir
        self.agents_config = self._load_yaml("agents.yaml")
        self.tasks_config = self._load_yaml("tasks.yaml")
        self.crews_config = self._load_yaml("crews.yaml")
        self.cost_tracking_enabled = True
        self.session_costs = []
        
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def create_agent(self, agent_name: str, llm=None) -> Agent:
        """Create an agent from YAML configuration"""
        if agent_name not in self.agents_config:
            raise ValueError(f"Agent '{agent_name}' not found in agents.yaml")
        
        config = self.agents_config[agent_name]
        
        return Agent(
            role=config.get("role"),
            goal=config.get("goal"),
            backstory=config.get("backstory"),
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            max_iter=config.get("max_iter", 3),
            max_execution_time=config.get("max_execution_time", 300),
            llm=llm
        )
    
    def create_task(self, task_name: str, agent: Agent, **kwargs) -> Task:
        """Create a task from YAML configuration"""
        if task_name not in self.tasks_config:
            raise ValueError(f"Task '{task_name}' not found in tasks.yaml")
        
        config = self.tasks_config[task_name]
        
        # Format description with provided kwargs
        description = config.get("description", "").format(**kwargs)
        
        return Task(
            description=description,
            expected_output=config.get("expected_output"),
            agent=agent
        )
    
    def create_crew(self, crew_name: str, agents: List[Agent], tasks: List[Task]) -> Crew:
        """Create a crew from YAML configuration"""
        if crew_name not in self.crews_config:
            raise ValueError(f"Crew '{crew_name}' not found in crews.yaml")
        
        config = self.crews_config[crew_name]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=config.get("process", "sequential"),
            verbose=config.get("verbose", True),
            memory=config.get("memory", False),
            cache=config.get("cache", True),
            max_rpm=config.get("max_rpm", 10),
            share_crew=config.get("share_crew", False)
        )
    
    def track_crew_costs(self, crew_result: Any, agent_name: str, model: str = "gpt-4", 
                        task_description: Optional[str] = None) -> Dict[str, Any]:
        """Track costs for a crew execution"""
        if not self.cost_tracking_enabled:
            return {}
        
        # Extract token usage from crew result if available
        # This is a simplified version - actual implementation would need to 
        # aggregate token usage from all agents in the crew
        token_usage = TokenUsage(
            prompt_tokens=1000,  # Placeholder - actual values would come from crew
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost_estimate = cost_tracker.track_usage(
            agent_name=agent_name,
            model=model,
            token_usage=token_usage,
            task_description=task_description or "Crew execution"
        )
        
        self.session_costs.append(cost_estimate)
        
        return {
            "cost_estimate": cost_estimate.dict(),
            "session_total": self.get_session_cost_summary()
        }
    
    def get_session_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for current session"""
        if not self.session_costs:
            return {"total_cost": 0.0, "total_tokens": 0, "requests": 0}
        
        total_cost = sum(cost.estimated_cost for cost in self.session_costs)
        total_tokens = sum(cost.token_usage.total_tokens for cost in self.session_costs)
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests": len(self.session_costs),
            "currency": "USD"
        }
    
    def enable_cost_tracking(self, enabled: bool = True):
        """Enable or disable cost tracking"""
        self.cost_tracking_enabled = enabled
        logger.info(f"Cost tracking {'enabled' if enabled else 'disabled'} for {self.__class__.__name__}")