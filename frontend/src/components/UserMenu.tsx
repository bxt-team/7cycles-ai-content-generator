import React, { useState } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Typography,
  Divider,
  Box,
  ListItemIcon,
  ListItemText,
  Chip
} from '@mui/material';
import {
  AccountCircle as AccountCircleIcon,
  Settings as SettingsIcon,
  Business as BusinessIcon,
  ExitToApp as LogoutIcon,
  Person as PersonIcon,
  Folder as FolderIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import { useOrganization } from '../contexts/OrganizationContext';
import { useTranslation } from 'react-i18next';

const UserMenu: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, signOut } = useSupabaseAuth();
  const { organizations, currentOrganization, setCurrentOrganization } = useOrganization();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleClose();
    await signOut();
    navigate('/login');
  };

  const handleNavigate = (path: string) => {
    handleClose();
    navigate(path);
  };

  if (!user) return null;

  // Get initials for avatar
  const getInitials = (email: string) => {
    if (!email) return '?';
    return email[0].toUpperCase();
  };

  return (
    <>
      <IconButton
        onClick={handleClick}
        size="small"
        sx={{ ml: 2 }}
        aria-controls={open ? 'user-menu' : undefined}
        aria-haspopup="true"
        aria-expanded={open ? 'true' : undefined}
      >
        <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
          {user.email ? getInitials(user.email) : <AccountCircleIcon />}
        </Avatar>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        id="user-menu"
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        PaperProps={{
          elevation: 3,
          sx: {
            overflow: 'visible',
            filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
            mt: 1.5,
            '& .MuiAvatar-root': {
              width: 32,
              height: 32,
              ml: -0.5,
              mr: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle1" noWrap>
            {user.user_metadata?.name || user.email?.split('@')[0] || t('userMenu.user')}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {user.email}
          </Typography>
        </Box>
        
        <Divider />
        
        <MenuItem onClick={() => handleNavigate('/profile')}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>{t('userMenu.myProfile')}</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => handleNavigate('/account-settings')}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>{t('userMenu.accountSettings')}</ListItemText>
        </MenuItem>
        
        <Divider />
        
        {/* Organization Selector */}
        {organizations && organizations.length > 0 && (
          <>
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontSize: '0.75rem' }}>
                {t('userMenu.organization')}
              </Typography>
            </Box>
            {organizations.map((org) => (
              <MenuItem 
                key={org.id} 
                onClick={() => {
                  setCurrentOrganization(org);
                  handleClose();
                }}
                selected={currentOrganization?.id === org.id}
              >
                <ListItemIcon>
                  <BusinessIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{org.name}</ListItemText>
                {currentOrganization?.id === org.id && (
                  <Chip size="small" label="Current" color="primary" sx={{ ml: 1, height: 20 }} />
                )}
              </MenuItem>
            ))}
            <MenuItem onClick={() => handleNavigate('/organization-settings')}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('userMenu.manageOrganizations')}</ListItemText>
            </MenuItem>
            <Divider />
          </>
        )}
        
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>{t('userMenu.signOut')}</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};

export default UserMenu;