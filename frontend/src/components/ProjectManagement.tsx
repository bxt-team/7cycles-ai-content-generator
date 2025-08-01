import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Tabs,
  Tab,
  Box,
  TextField,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  ListItemAvatar,
  Avatar
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PersonAdd as PersonAddIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Folder as FolderIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { apiService } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProjectManagement: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useSupabaseAuth();
  const { currentOrganization } = useOrganization();
  const currentProject: any = null;
  const setCurrentProject = (project: any) => {};
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Projects list
  const [projects, setProjects] = useState<any[]>([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  
  // Project details
  const [projectDetails, setProjectDetails] = useState<any>(null);
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  
  // Members
  const [projectMembers, setProjectMembers] = useState<any[]>([]);
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState('member');
  const [organizationMembers, setOrganizationMembers] = useState<any[]>([]);

  useEffect(() => {
    if (currentOrganization) {
      loadProjects();
      if (tabValue === 2) {
        loadOrganizationMembers();
      }
    }
  }, [currentOrganization]);

  useEffect(() => {
    if (currentProject && tabValue > 0) {
      loadProjectData();
    }
  }, [currentProject, tabValue]);

  const loadProjects = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.list(currentOrganization.id);
      setProjects(response.data.projects || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading projects');
    } finally {
      setLoading(false);
    }
  };

  const loadProjectData = async () => {
    if (!currentProject) return;
    
    setLoading(true);
    setError('');
    
    try {
      switch (tabValue) {
        case 1: // Details
          const detailsResponse = await apiService.projects.get(currentProject.id);
          setProjectDetails(detailsResponse.data.project);
          break;
        case 2: // Members
          const membersResponse = await apiService.projects.getMembers(currentProject.id);
          setProjectMembers(membersResponse.data.members);
          break;
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const loadOrganizationMembers = async () => {
    if (!currentOrganization) return;
    
    try {
      const response = await apiService.organizations.getMembers(currentOrganization.id);
      setOrganizationMembers(response.data.members);
    } catch (err: any) {
      console.error('Error loading organization members:', err);
    }
  };

  const handleCreateProject = async () => {
    if (!currentOrganization || !newProjectName.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await apiService.projects.create({
        name: newProjectName,
        description: newProjectDescription,
        organization_id: currentOrganization.id
      });
      
      setSuccess('Project successfully created');
      setCreateDialogOpen(false);
      setNewProjectName('');
      setNewProjectDescription('');
      loadProjects();
      
      // Set as current project
      setCurrentProject(response.data.project);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error creating project');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = (project: any) => {
    setCurrentProject(project);
    localStorage.setItem('currentProjectId', project.id);
    setSuccess(`Project "${project.name}" selected`);
  };

  const handleSaveDetails = async () => {
    if (!currentProject || !projectDetails) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.update(currentProject.id, {
        name: projectDetails.name,
        description: projectDetails.description,
        settings: projectDetails.settings
      });
      
      setSuccess('Project successfully updated');
      setIsEditingDetails(false);
      
      // Update current project in context
      setCurrentProject({ ...currentProject, name: projectDetails.name });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error saving');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = async () => {
    if (!currentProject || !selectedUserId) return;
    
    setLoading(true);
    setError('');
    
    try {
      await apiService.projects.addMember(currentProject.id, {
        user_id: selectedUserId,
        role: selectedRole
      });
      
      setSuccess('Member added successfully');
      setAddMemberDialogOpen(false);
      setSelectedUserId('');
      setSelectedRole('member');
      loadProjectData(); // Reload members
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error adding member');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!currentProject) return;
    
    if (!window.confirm('Are you sure you want to remove this member from the project?')) return;
    
    try {
      // Note: This endpoint might need to be added to the backend
      await apiService.projects.delete(`${currentProject.id}/members/${memberId}`);
      setSuccess('Member removed successfully');
      loadProjectData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error removing member');
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) return;
    
    try {
      await apiService.projects.delete(projectId);
      setSuccess('Project successfully deleted');
      
      // If deleted project was current, clear selection
      if (currentProject?.id === projectId) {
        setCurrentProject(null);
        localStorage.removeItem('currentProjectId');
      }
      
      loadProjects();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error deleting project');
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'owner': return 'error';
      case 'admin': return 'warning';
      case 'member': return 'primary';
      case 'viewer': return 'default';
      default: return 'default';
    }
  };

  const getAvailableMembers = () => {
    // Filter out members who are already in the project
    const projectMemberIds = projectMembers.map(m => m.id);
    return organizationMembers.filter(m => !projectMemberIds.includes(m.id));
  };

  if (!currentOrganization) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="info">Please select an organization</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
            <Tab label="Projects" icon={<FolderIcon />} iconPosition="start" />
            <Tab 
              label="Details" 
              icon={<EditIcon />} 
              iconPosition="start"
              disabled={!currentProject}
            />
            <Tab 
              label="Members" 
              icon={<GroupIcon />} 
              iconPosition="start"
              disabled={!currentProject}
            />
          </Tabs>
        </Box>

        {error && <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ m: 2 }}>{success}</Alert>}

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Projects in {currentOrganization.name}</Typography>
              <Button
                startIcon={<AddIcon />}
                variant="contained"
                onClick={() => setCreateDialogOpen(true)}
              >
                New Project
              </Button>
            </Box>

            {loading ? (
              <CircularProgress />
            ) : projects.length === 0 ? (
              <Alert severity="info">
                No projects yet. Create your first project!
              </Alert>
            ) : (
              <Grid container spacing={3}>
                {projects.map((project) => (
                  <Grid size={{ xs: 12, md: 6, lg: 4 }} key={project.id}>
                    <Card 
                      sx={{ 
                        cursor: 'pointer',
                        border: currentProject?.id === project.id ? 2 : 0,
                        borderColor: 'primary.main'
                      }}
                      onClick={() => handleSelectProject(project)}
                    >
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="start">
                          <Box>
                            <Typography variant="h6" gutterBottom>
                              {project.name}
                            </Typography>
                            <Typography variant="body2" color="textSecondary" paragraph>
                              {project.description || 'Keine Beschreibung'}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Erstellt: {new Date(project.created_at).toLocaleDateString('de-DE')}
                            </Typography>
                          </Box>
                          <Box>
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/projects/${project.id}`);
                              }}
                              title="View Details"
                            >
                              <VisibilityIcon />
                            </IconButton>
                            {project.role === 'owner' && (
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteProject(project.id);
                                }}
                                color="error"
                                title="Delete Project"
                              >
                                <DeleteIcon />
                              </IconButton>
                            )}
                          </Box>
                        </Box>
                        {currentProject?.id === project.id && (
                          <Chip
                            label="Aktiv"
                            color="primary"
                            size="small"
                            sx={{ mt: 1 }}
                          />
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {loading ? (
            <CircularProgress />
          ) : projectDetails ? (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h5">Project Details</Typography>
                {!isEditingDetails ? (
                  <IconButton onClick={() => setIsEditingDetails(true)}>
                    <EditIcon />
                  </IconButton>
                ) : (
                  <Button
                    startIcon={<SaveIcon />}
                    variant="contained"
                    onClick={handleSaveDetails}
                    disabled={loading}
                  >
                    Save
                  </Button>
                )}
              </Box>

              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Name"
                    value={projectDetails.name || ''}
                    onChange={(e) => setProjectDetails({ ...projectDetails, name: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid size={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="Beschreibung"
                    value={projectDetails.description || ''}
                    onChange={(e) => setProjectDetails({ ...projectDetails, description: e.target.value })}
                    disabled={!isEditingDetails}
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Erstellt am"
                    value={new Date(projectDetails.created_at).toLocaleDateString('de-DE')}
                    disabled
                  />
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                  <TextField
                    fullWidth
                    label="Your Role"
                    value={projectDetails.role || 'member'}
                    disabled
                  />
                </Grid>
              </Grid>
            </Box>
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h5">Project Members</Typography>
              <Button
                startIcon={<PersonAddIcon />}
                variant="contained"
                onClick={() => {
                  loadOrganizationMembers();
                  setAddMemberDialogOpen(true);
                }}
              >
                Add Member
              </Button>
            </Box>

            {loading ? (
              <CircularProgress />
            ) : (
              <List>
                {projectMembers.map((member) => (
                  <ListItem key={member.id}>
                    <ListItemAvatar>
                      <Avatar>
                        <PersonIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={member.name}
                      secondary={
                        <React.Fragment>
                          {member.email}
                          <Chip
                            label={member.role}
                            color={getRoleColor(member.role)}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        </React.Fragment>
                      }
                    />
                    {member.role !== 'owner' && currentProject?.role === 'owner' && (
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveMember(member.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    )}
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        </TabPanel>
      </Paper>

      {/* Create Project Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            variant="outlined"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && newProjectName.trim() && !loading) {
                handleCreateProject();
              }
            }}
          />
          <TextField
            margin="dense"
            label="Description (optional)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={newProjectDescription}
            onChange={(e) => setNewProjectDescription(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && newProjectName.trim() && !loading) {
                e.preventDefault();
                handleCreateProject();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleCreateProject} 
            variant="contained" 
            disabled={!newProjectName.trim() || loading}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Member Dialog */}
      <Dialog open={addMemberDialogOpen} onClose={() => setAddMemberDialogOpen(false)}>
        <DialogTitle>Add Member</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Select Member</InputLabel>
            <Select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              label="Select Member"
            >
              {getAvailableMembers().map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name} ({member.email})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Role</InputLabel>
            <Select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              label="Role"
            >
              <MenuItem value="viewer">Viewer</MenuItem>
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="admin">Administrator</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleAddMember} 
            variant="contained" 
            disabled={!selectedUserId || loading}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ProjectManagement;