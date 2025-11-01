"""Agent skills definitions for the Administration Agent."""
from a2a.types import AgentSkill


def get_public_skills() -> list[AgentSkill]:
    """
    Get the list of public skills for the Administration Agent.
    
    These skills are available in the public agent card.
    
    Returns:
        List of AgentSkill instances for public access
    """
    account_management_skill = AgentSkill(
        id='account_management',
        name='Account Management',
        description=(
            'Handle account creation, deletion, and closure requests. '
            'Requires confirmation step with verification data before execution.'
        ),
        tags=['account', 'delete', 'create', 'closure', 'confirmation'],
        examples=[
            'I need to delete my account',
            'How do I create a new account?',
            'I want to close my account',
            'Yes, I confirm. Email: user@example.com',
            'Yes, proceed with deletion. My email is user@example.com'
        ],
    )
    
    profile_management_skill = AgentSkill(
        id='profile_management',
        name='Profile Management',
        description=(
            'Update user profile information including email and name changes. '
            'Requires confirmation with current and new values before execution.'
        ),
        tags=['profile', 'email', 'name', 'update', 'confirmation'],
        examples=[
            'I want to change my email address',
            'How do I update my name?',
            'Yes, update my email. Current: old@example.com, New: new@example.com',
            'Yes, proceed. Current name: John Smith, New name: John Doe'
        ],
    )
    
    permissions_skill = AgentSkill(
        id='permissions_management',
        name='Permissions and Roles',
        description='Manage user permissions, roles, and access control. Query role information without confirmation.',
        tags=['permission', 'role', 'access', 'authorization'],
        examples=[
            'What permissions does the Developer role have?',
            'How do I change user permissions?',
            'What roles are available?'
        ],
    )
    
    team_management_skill = AgentSkill(
        id='team_management',
        name='Team Management',
        description=(
            'Add or remove team members, manage team settings. '
            'Requires confirmation with member details (email, role) before execution.'
        ),
        tags=['team', 'member', 'add', 'remove', 'invite', 'confirmation'],
        examples=[
            'How do I add team members?',
            'I need to remove a team member',
            'Yes, send invitation. Email: member@example.com, Role: Developer',
            'Yes, I confirm. Remove: member@example.com'
        ],
    )
    
    return [
        account_management_skill,
        profile_management_skill,
        permissions_skill,
        team_management_skill,
    ]


def get_extended_skills() -> list[AgentSkill]:
    """
    Get the list of extended skills for authenticated users.
    
    These skills are available in the extended agent card and include
    the public skills plus additional enterprise features.
    
    Returns:
        List of AgentSkill instances including public and extended skills
    """
    # Get public skills first
    public_skills = get_public_skills()
    
    # Define extended-only skills
    organization_management_skill = AgentSkill(
        id='organization_management',
        name='Organization Settings',
        description=(
            'Manage organization settings, sub-accounts, and organization-wide configurations. '
            'Requires confirmation before applying changes.'
        ),
        tags=['organization', 'org', 'settings', 'sub-account', 'enterprise', 'confirmation'],
        examples=[
            'How do I manage organization settings?',
            'I need to create a sub-account',
            'What organization settings are available?',
            'Yes, proceed with organization settings update'
        ],
    )
    
    advanced_permissions_skill = AgentSkill(
        id='advanced_permissions',
        name='Advanced Permissions',
        description=(
            'Advanced permission management including custom roles and fine-grained access control. '
            'Requires confirmation with role/permission details before execution.'
        ),
        tags=['permission', 'role', 'custom', 'advanced', 'fine-grained', 'confirmation'],
        examples=[
            'How do I create a custom role?',
            'I need to set up fine-grained permissions',
            'What advanced permission options are available?',
            'Yes, create custom role. Name: CustomEditor, Permissions: read,write'
        ],
    )
    
    # Return all skills (public + extended)
    return [
        *public_skills,
        organization_management_skill,
        advanced_permissions_skill,
    ]


# Export individual skills if needed for direct access
__all__ = ['get_public_skills', 'get_extended_skills']

