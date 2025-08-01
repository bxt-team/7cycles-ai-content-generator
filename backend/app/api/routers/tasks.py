from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, date
import json

from supabase import create_client, Client
import os
from ...core.supabase_auth import get_current_user
from ...core.dependencies import get_task_suggestion_crew
from ...agents.crews.task_suggestion_crew import TaskSuggestionInput, TaskSuggestionOutput

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


class TaskCreate(BaseModel):
    goal_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high|urgent)$")
    assigned_to_type: Optional[str] = Field(None, pattern="^(member|agent)$")
    assigned_to_id: Optional[UUID] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    assigned_to_type: Optional[str] = Field(None, pattern="^(member|agent)$")
    assigned_to_id: Optional[UUID] = None
    due_date: Optional[date] = None


class TaskAssign(BaseModel):
    assigned_to_type: str = Field(..., pattern="^(member|agent)$")
    assigned_to_id: UUID


class Task(BaseModel):
    id: UUID
    goal_id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    assigned_to_type: Optional[str]
    assigned_to_id: Optional[UUID]
    assigned_to_name: Optional[str]
    created_by_type: str
    created_by_id: Optional[UUID]
    created_by_name: Optional[str]
    due_date: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    goal_title: Optional[str] = None
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None


class TaskHistory(BaseModel):
    id: UUID
    task_id: UUID
    action: str
    actor_type: str
    actor_id: Optional[UUID]
    actor_name: Optional[str]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    created_at: datetime


async def verify_goal_access(goal_id: str, user_id: str, supabase) -> bool:
    """Verify user has access to the goal's project."""
    try:
        # Get the goal's project
        goal = supabase.table('goals').select('project_id').eq(
            'id', goal_id
        ).single().execute()
        
        if not goal.data:
            return False
        
        # Check if user is a member of the project
        member_check = supabase.table('project_members').select('role').eq(
            'project_id', goal.data['project_id']
        ).eq('user_id', user_id).execute()
        
        if member_check.data:
            return True
        
        # Check if user is member of organization that owns the project
        project_org = supabase.table('projects').select('organization_id').eq(
            'id', goal.data['project_id']
        ).single().execute()
        
        if project_org.data:
            org_member_check = supabase.table('organization_members').select('role').eq(
                'organization_id', project_org.data['organization_id']
            ).eq('user_id', user_id).execute()
            
            return bool(org_member_check.data)
        
        return False
    except:
        return False


async def get_actor_name(actor_type: str, actor_id: str, supabase) -> str:
    """Get the name of an actor (member or agent)."""
    try:
        if actor_type == 'member':
            user = supabase.auth.admin.get_user_by_id(actor_id)
            if user and user.user:
                return user.user.user_metadata.get('full_name', user.user.email)
            return 'Unknown Member'
        elif actor_type == 'agent':
            # For now, we'll use the agent ID as the name
            # In the future, this could lookup agent configurations
            return f"Agent-{actor_id[:8]}"
        else:
            return 'System'
    except:
        return 'Unknown'


async def create_task_history(
    task_id: str,
    action: str,
    actor_type: str,
    actor_id: Optional[str],
    actor_name: Optional[str],
    old_value: Optional[Dict[str, Any]],
    new_value: Optional[Dict[str, Any]],
    supabase
):
    """Create a task history entry."""
    history_data = {
        'task_id': task_id,
        'action': action,
        'actor_type': actor_type,
        'actor_id': actor_id,
        'actor_name': actor_name,
        'old_value': old_value,
        'new_value': new_value
    }
    
    supabase.table('task_history').insert(history_data).execute()


@router.get("", response_model=List[Task])
async def list_tasks(
    goal_id: Optional[UUID] = None,
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    assigned_to_me: Optional[bool] = False,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List tasks. Can filter by goal, project, status, or assigned to current user."""
    supabase = get_supabase()
    
    try:
        # Get the user ID from the auth context
        auth_email = current_user.get('email')
        user_id = str(current_user['user_id'])
        
        # Get the public user ID from the users table if needed
        if auth_email:
            user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
            if user_result.data:
                user_id = user_result.data[0]['id']
        
        # Build query
        query = supabase.table('tasks').select(
            '*, goals!inner(id, title, project_id, projects!inner(id, name))'
        )
        
        if goal_id:
            # Verify access to specific goal
            if not await verify_goal_access(str(goal_id), user_id, supabase):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this goal"
                )
            query = query.eq('goal_id', str(goal_id))
        elif project_id:
            # Filter by project - join through goals
            query = query.eq('goals.project_id', str(project_id))
        else:
            # Get all accessible tasks through project membership
            # First get projects user has access to
            member_projects = supabase.table('project_members').select('project_id').eq(
                'user_id', user_id
            ).execute()
            
            org_memberships = supabase.table('organization_members').select('organization_id').eq(
                'user_id', user_id
            ).execute()
            
            project_ids = [m['project_id'] for m in member_projects.data]
            
            if org_memberships.data:
                org_ids = [m['organization_id'] for m in org_memberships.data]
                org_projects = supabase.table('projects').select('id').in_(
                    'organization_id', org_ids
                ).execute()
                project_ids.extend([p['id'] for p in org_projects.data])
            
            if not project_ids:
                return []
            
            # Get goals for these projects
            goals_response = supabase.table('goals').select('id').in_(
                'project_id', list(set(project_ids))
            ).execute()
            
            goal_ids = [g['id'] for g in goals_response.data]
            if not goal_ids:
                return []
            
            query = query.in_('goal_id', goal_ids)
        
        if status:
            query = query.eq('status', status)
        
        if assigned_to_me:
            # Filter tasks assigned to the current user
            query = query.eq('assigned_to_type', 'member').eq(
                'assigned_to_id', user_id
            )
        
        response = query.order('created_at', desc=True).execute()
        
        tasks = []
        for task in response.data:
            task_dict = dict(task)
            
            if task.get('goals'):
                task_dict['goal_title'] = task['goals']['title']
                if task['goals'].get('projects'):
                    task_dict['project_id'] = task['goals']['projects']['id']
                    task_dict['project_name'] = task['goals']['projects']['name']
                del task_dict['goals']
            
            tasks.append(Task(**task_dict))
        
        return tasks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    created_by_type: str = "member",  # Can be overridden by agents
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new task."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Verify user has access to the goal
    if not await verify_goal_access(str(task.goal_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this goal"
        )
    
    try:
        # Get creator name
        creator_name = await get_actor_name(created_by_type, user_id, supabase)
        
        # Get assignee name if assigned
        assigned_to_name = None
        if task.assigned_to_id and task.assigned_to_type:
            assigned_to_name = await get_actor_name(
                task.assigned_to_type, 
                str(task.assigned_to_id), 
                supabase
            )
        
        task_data = {
            'goal_id': str(task.goal_id),
            'title': task.title,
            'description': task.description,
            'status': 'pending',
            'priority': task.priority,
            'assigned_to_type': task.assigned_to_type,
            'assigned_to_id': str(task.assigned_to_id) if task.assigned_to_id else None,
            'assigned_to_name': assigned_to_name,
            'created_by_type': created_by_type,
            'created_by_id': user_id,
            'created_by_name': creator_name,
            'due_date': task.due_date.isoformat() if task.due_date else None
        }
        
        response = supabase.table('tasks').insert(task_data).execute()
        created_task = response.data[0]
        
        # Create history entry
        await create_task_history(
            created_task['id'],
            'created',
            created_by_type,
            user_id,
            creator_name,
            None,
            task_data,
            supabase
        )
        
        # Get with goal and project info
        task_response = supabase.table('tasks').select(
            '*, goals!inner(title, projects!inner(id, name))'
        ).eq('id', created_task['id']).single().execute()
        
        task_dict = dict(task_response.data)
        
        if task_dict.get('goals'):
            task_dict['goal_title'] = task_dict['goals']['title']
            if task_dict['goals'].get('projects'):
                task_dict['project_id'] = task_dict['goals']['projects']['id']
                task_dict['project_name'] = task_dict['goals']['projects']['name']
            del task_dict['goals']
        
        return Task(**task_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific task."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('tasks').select(
            '*, goals!inner(id, title, project_id, projects!inner(id, name))'
        ).eq('id', str(task_id)).single().execute()
        
        task_dict = dict(response.data)
        
        # Get the user ID from the auth context
        auth_email = current_user.get('email')
        user_id = str(current_user['user_id'])
        
        # Get the public user ID from the users table if needed
        if auth_email:
            user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
            if user_result.data:
                user_id = user_result.data[0]['id']
        
        # Verify user has access to the goal
        if not await verify_goal_access(task_dict['goal_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if task_dict.get('goals'):
            task_dict['goal_title'] = task_dict['goals']['title']
            if task_dict['goals'].get('projects'):
                task_dict['project_id'] = task_dict['goals']['projects']['id']
                task_dict['project_name'] = task_dict['goals']['projects']['name']
            del task_dict['goals']
        
        return Task(**task_dict)
    except Exception as e:
        if 'No rows found' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.patch("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID,
    task: TaskUpdate,
    actor_type: str = "member",  # Can be overridden by agents
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a task."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Get the task to verify access and track changes
    try:
        task_check = supabase.table('tasks').select('*').eq(
            'id', str(task_id)
        ).single().execute()
        
        if not await verify_goal_access(task_check.data['goal_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        old_task = dict(task_check.data)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    update_data = {}
    changes = {}
    
    if task.title is not None and task.title != old_task['title']:
        update_data['title'] = task.title
        changes['title'] = {'old': old_task['title'], 'new': task.title}
    
    if task.description is not None and task.description != old_task.get('description'):
        update_data['description'] = task.description
        changes['description'] = {'old': old_task.get('description'), 'new': task.description}
    
    if task.status is not None and task.status != old_task['status']:
        update_data['status'] = task.status
        changes['status'] = {'old': old_task['status'], 'new': task.status}
        if task.status == 'completed':
            update_data['completed_at'] = datetime.utcnow().isoformat()
    
    if task.priority is not None and task.priority != old_task['priority']:
        update_data['priority'] = task.priority
        changes['priority'] = {'old': old_task['priority'], 'new': task.priority}
    
    if task.due_date is not None:
        new_due_date = task.due_date.isoformat() if task.due_date else None
        if new_due_date != old_task.get('due_date'):
            update_data['due_date'] = new_due_date
            changes['due_date'] = {'old': old_task.get('due_date'), 'new': new_due_date}
    
    # Handle assignment changes
    if task.assigned_to_type is not None or task.assigned_to_id is not None:
        old_assignment = {
            'type': old_task.get('assigned_to_type'),
            'id': old_task.get('assigned_to_id'),
            'name': old_task.get('assigned_to_name')
        }
        
        new_type = task.assigned_to_type if task.assigned_to_type is not None else old_task.get('assigned_to_type')
        new_id = str(task.assigned_to_id) if task.assigned_to_id else None
        
        if new_type != old_assignment['type'] or new_id != old_assignment['id']:
            assigned_to_name = None
            if new_id and new_type:
                assigned_to_name = await get_actor_name(new_type, new_id, supabase)
            
            update_data['assigned_to_type'] = new_type
            update_data['assigned_to_id'] = new_id
            update_data['assigned_to_name'] = assigned_to_name
            
            changes['assignment'] = {
                'old': old_assignment,
                'new': {
                    'type': new_type,
                    'id': new_id,
                    'name': assigned_to_name
                }
            }
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('tasks').update(update_data).eq(
            'id', str(task_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Create history entry
        actor_name = await get_actor_name(actor_type, user_id, supabase)
        await create_task_history(
            str(task_id),
            'updated',
            actor_type,
            user_id,
            actor_name,
            changes,
            update_data,
            supabase
        )
        
        # Get with goal and project info
        task_response = supabase.table('tasks').select(
            '*, goals!inner(title, projects!inner(id, name))'
        ).eq('id', str(task_id)).single().execute()
        
        task_dict = dict(task_response.data)
        
        if task_dict.get('goals'):
            task_dict['goal_title'] = task_dict['goals']['title']
            if task_dict['goals'].get('projects'):
                task_dict['project_id'] = task_dict['goals']['projects']['id']
                task_dict['project_name'] = task_dict['goals']['projects']['name']
            del task_dict['goals']
        
        return Task(**task_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.post("/{task_id}/assign", response_model=Task)
async def assign_task(
    task_id: UUID,
    assignment: TaskAssign,
    actor_type: str = "member",  # Can be overridden by agents
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Assign a task to a member or agent."""
    # This is a convenience endpoint that calls update_task
    task_update = TaskUpdate(
        assigned_to_type=assignment.assigned_to_type,
        assigned_to_id=assignment.assigned_to_id
    )
    
    return await update_task(task_id, task_update, actor_type, current_user)


@router.get("/{task_id}/history", response_model=List[TaskHistory])
async def get_task_history(
    task_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get the history of changes for a task."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Verify access through the task's goal
    try:
        task_check = supabase.table('tasks').select('goal_id').eq(
            'id', str(task_id)
        ).single().execute()
        
        if not await verify_goal_access(task_check.data['goal_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    try:
        response = supabase.table('task_history').select('*').eq(
            'task_id', str(task_id)
        ).order('created_at', desc=True).execute()
        
        return [TaskHistory(**h) for h in response.data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task history: {str(e)}"
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a task."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Get the task to verify access
    try:
        task_check = supabase.table('tasks').select('goal_id').eq(
            'id', str(task_id)
        ).single().execute()
        
        if not await verify_goal_access(task_check.data['goal_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    try:
        # Delete task (history will be cascade deleted)
        response = supabase.table('tasks').delete().eq(
            'id', str(task_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )

class TaskSuggestionRequest(BaseModel):
    goal_id: UUID
    custom_prompt: Optional[str] = None
    session_id: Optional[UUID] = None


class TaskSuggestionFeedback(BaseModel):
    goal_id: UUID
    session_id: UUID
    suggested_tasks: List[Dict[str, Any]]
    feedback: List[Dict[str, Any]]


@router.post("/suggest", response_model=TaskSuggestionOutput)
async def suggest_tasks(
    request: TaskSuggestionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    task_crew = Depends(get_task_suggestion_crew)
):
    """Generate AI-powered task suggestions based on a goal."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get("email")
    user_id = str(current_user["user_id"])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]["id"]
    
    # Verify user has access to the goal
    if not await verify_goal_access(str(request.goal_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this goal"
        )
    
    try:
        # Get goal details
        goal_response = supabase.table("goals").select(
            "*, projects\!inner(id, name, description)"
        ).eq("id", str(request.goal_id)).single().execute()
        
        if not goal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        goal = goal_response.data
        project = goal.get("projects", {})
        
        # Get existing tasks for context
        existing_tasks_response = supabase.table("tasks").select(
            "title, description, status, priority"
        ).eq("goal_id", str(request.goal_id)).execute()
        
        existing_tasks = existing_tasks_response.data if existing_tasks_response.data else []
        
        # Get historical feedback for the crew
        historical_feedback = None
        try:
            feedback_data = supabase.table("task_suggestion_feedback").select(
                "rating, feedback_type, feedback_text"
            ).eq("goal_id", str(request.goal_id)).order(
                "created_at", desc=True
            ).limit(20).execute()
            
            if feedback_data.data:
                ratings = [f["rating"] for f in feedback_data.data if f.get("rating")]
                historical_feedback = {
                    "average_rating": sum(ratings) / len(ratings) if ratings else 0,
                    "total_feedback": len(feedback_data.data),
                    "recent_feedback": feedback_data.data[:5]
                }
        except:
            pass
        
        # Prepare input for the crew
        crew_input = TaskSuggestionInput(
            goal_title=goal.get("title", ""),
            goal_description=goal.get("description", ""),
            goal_target_date=goal.get("target_date"),
            project_description=project.get("description", ""),
            existing_tasks=existing_tasks,
            custom_prompt=request.custom_prompt,
            historical_feedback=historical_feedback
        )
        
        # Generate suggestions
        result = task_crew.suggest_tasks(crew_input)
        
        # Generate session ID if not provided
        session_id = request.session_id or uuid4()
        
        # Add session_id to the response
        result_dict = result.dict() if hasattr(result, "dict") else result
        result_dict["session_id"] = str(session_id)
        
        return result_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate task suggestions: {str(e)}"
        )


@router.post("/suggest/feedback", status_code=status.HTTP_201_CREATED)
async def submit_task_suggestion_feedback(
    feedback: TaskSuggestionFeedback,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit feedback on AI-generated task suggestions."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get("email")
    user_id = str(current_user["user_id"])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]["id"]
    
    # Verify user has access to the goal
    if not await verify_goal_access(str(feedback.goal_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this goal"
        )
    
    try:
        # Process each feedback item
        feedback_records = []
        for fb_item in feedback.feedback:
            task_index = fb_item.get("task_index", 0)
            
            # Validate task index
            if task_index >= len(feedback.suggested_tasks):
                continue
            
            suggested_task = feedback.suggested_tasks[task_index]
            
            feedback_record = {
                "goal_id": str(feedback.goal_id),
                "user_id": user_id,
                "suggestion_session_id": str(feedback.session_id),
                "suggested_task": json.dumps(suggested_task),
                "feedback_type": fb_item.get("feedback_type", "neutral"),
                "rating": fb_item.get("rating"),
                "feedback_text": fb_item.get("feedback_text"),
                "created_at": datetime.utcnow().isoformat()
            }
            
            feedback_records.append(feedback_record)
        
        # Insert feedback records
        if feedback_records:
            supabase.table("task_suggestion_feedback").insert(feedback_records).execute()
        
        return {"message": "Feedback submitted successfully", "count": len(feedback_records)}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/summary")
async def get_task_feedback_summary(
    goal_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get summary of feedback for task suggestions for a goal."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get("email")
    user_id = str(current_user["user_id"])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]["id"]
    
    # Verify user has access to the goal
    if not await verify_goal_access(str(goal_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this goal"
        )
    
    try:
        feedback_data = supabase.table("task_suggestion_feedback").select(
            "rating, feedback_type"
        ).eq("goal_id", str(goal_id)).execute()
        
        if not feedback_data.data:
            return {"total_feedback": 0, "average_rating": 0, "feedback_types": {}}
        
        ratings = [f["rating"] for f in feedback_data.data if f.get("rating")]
        feedback_types = {}
        
        for f in feedback_data.data:
            ft = f.get("feedback_type", "neutral")
            feedback_types[ft] = feedback_types.get(ft, 0) + 1
        
        return {
            "total_feedback": len(feedback_data.data),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "feedback_types": feedback_types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback summary: {str(e)}"
        )

