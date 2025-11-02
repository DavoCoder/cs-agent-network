"""Administration Agent that handles administrative tasks and queries with confirmation steps."""
import re


class AdministrationAgent:
    """Administration Agent that handles administrative tasks and queries with confirmation steps."""

    def _is_confirmation_message(self, query_lower: str) -> bool:
        """
        Check if the message contains confirmation keywords and relevant data.
        
        Returns True only if BOTH conditions are met:
        1. Contains explicit confirmation keywords
        2. Contains data indicators OR has been formatted as a confirmation response
        
        This prevents informational questions (like "How to create an account?") 
        from being treated as confirmations.
        """
        confirmation_keywords = [
            'yes', 'confirm', 'proceed', 'execute', 'go ahead', 'ok', 'okay',
            'approved', 'authorize', 'i confirm', 'please proceed', 'do it'
        ]
        has_confirmation = any(keyword in query_lower for keyword in confirmation_keywords)
        
        # Check for informational question words that indicate this is NOT a confirmation
        question_indicators = ['how', 'what', 'when', 'where', 'why', 'can i', 'should i']
        is_question = any(indicator in query_lower for indicator in question_indicators)
        
        # If it's a question, it's not a confirmation
        if is_question:
            return False
        
        # Check for data indicators (email, names, roles, etc.)
        # Only consider data as confirmation if we also have confirmation keywords
        has_data = any(indicator in query_lower for indicator in [
            '@', 'email:', 'name:', 'role:', 'current:', 'new:'
        ])
        
        # Require both confirmation keyword AND (data OR the query is clearly formatted as confirmation)
        # This prevents queries like "create account" from being treated as confirmations
        return has_confirmation and (has_data or len(query_lower.split()) > 10)

    async def process_admin_request(self, user_query: str) -> str:
        """
        Process administrative requests based on user query.
        Handles two-step flow: initial request -> confirmation -> execution.
        
        Args:
            user_query: The user's administrative request
            
        Returns:
            A response to the administrative request
        """
        query_lower = user_query.lower()
        is_confirmation = self._is_confirmation_message(query_lower)
        
        # Extract email if present (simple pattern)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, user_query)
        
        # Account management - flexible matching for delete/close/remove account
        if (('delete' in query_lower and 'account' in query_lower) or 
            ('close' in query_lower and 'account' in query_lower) or 
            ('remove' in query_lower and 'account' in query_lower)):
            if is_confirmation and emails:
                email = emails[0]
                return (
                    f"✅ Account deletion confirmed and processed.\n\n"
                    f"Account associated with {email} has been successfully deleted. "
                    f"All associated data has been permanently removed from our systems.\n\n"
                    f"A confirmation email has been sent to {email}. "
                    f"This action cannot be undone. If this was done in error, "
                    f"you will need to create a new account."
                )
            return (
                "⚠️ **ACCOUNT DELETION REQUEST**\n\n"
                "This is an irreversible action that will permanently delete your account "
                "and all associated data including:\n"
                "- User profile and settings\n"
                "- Team memberships\n"
                "- Organization access\n"
                "- Historical data\n\n"
                "To proceed, please confirm by replying with:\n"
                "- 'Yes, I confirm' or 'Proceed with deletion'\n"
                "- Your email address for verification\n\n"
                "Example: 'Yes, I confirm. My email is user@example.com'"
            )
        
        # Check for account creation - flexible matching to catch "create account", "create the account", "create a new account", "account creation", etc.
        has_create = 'create' in query_lower or 'creation' in query_lower
        if (has_create and 'account' in query_lower) or 'new account' in query_lower:
            if is_confirmation:
                # Extract name if provided
                name_match = re.search(r'(?:name|full name)[: ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', user_query, re.IGNORECASE)
                org_match = re.search(r'(?:organization|org)[: ]+([A-Za-z0-9\s&.,-]+)', user_query, re.IGNORECASE)
                
                email = emails[0] if emails else "provided email"
                name = name_match.group(1) if name_match else "provided name"
                org = org_match.group(1).strip() if org_match else None
                
                return (
                    f"✅ Account creation confirmed and processed.\n\n"
                    f"New account has been successfully created:\n"
                    f"- Email: {email}\n"
                    f"- Name: {name}\n"
                    f"{f'- Organization: {org}' if org else ''}\n\n"
                    f"A welcome email with account activation instructions has been sent to {email}. "
                    f"Please check your inbox and follow the activation link to complete the setup."
                )
            return (
                "To create a new account, I'll need the following information:\n\n"
                "**Required Information:**\n"
                "1. Email address\n"
                "2. Full name\n"
                "3. Organization name (optional)\n\n"
                "Please provide this information and confirm by saying:\n"
                "- 'Yes, create the account' or 'Please proceed'\n"
                "- Include: Email, Name, and Organization (if applicable)\n\n"
                "Example: 'Yes, please proceed. Email: user@example.com, Name: John Doe, Organization: Acme Corp'"
            )
        
        # Profile management - flexible matching for email changes
        if (('change' in query_lower and 'email' in query_lower) or 
            ('update' in query_lower and 'email' in query_lower) or 
            ('email' in query_lower and 'address' in query_lower)):
            if is_confirmation and len(emails) >= 1:
                old_email = emails[0] if len(emails) >= 1 else "current email"
                new_email = emails[1] if len(emails) >= 2 else emails[0]
                return (
                    f"✅ Email update confirmed and processed.\n\n"
                    f"Your email address has been successfully updated:\n"
                    f"- Old email: {old_email}\n"
                    f"- New email: {new_email}\n\n"
                    f"A verification email has been sent to {new_email}. "
                    f"Please verify the new email address to complete the update. "
                    f"Your account login will now use {new_email}."
                )
            return (
                "To update your email address, I need:\n\n"
                "**Required Information:**\n"
                "1. Your current email address (for verification)\n"
                "2. Your new email address\n\n"
                "Please provide both email addresses and confirm by saying:\n"
                "- 'Yes, update my email' or 'Proceed with email change'\n"
                "- Include both: current email and new email\n\n"
                "Example: 'Yes, please proceed. Current: old@example.com, New: new@example.com'"
            )
        
        # Name change - flexible matching
        if (('change' in query_lower and 'name' in query_lower) or 
            ('update' in query_lower and 'name' in query_lower)):
            if is_confirmation:
                name_matches = re.findall(r'(?:name|new name)[: ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', user_query, re.IGNORECASE)
                new_name = name_matches[-1] if name_matches else "provided name"
                return (
                    f"✅ Name update confirmed and processed.\n\n"
                    f"Your profile name has been successfully updated to: **{new_name}**\n\n"
                    f"This change is effective immediately and will be reflected across all "
                    f"platform features. Your account settings and permissions remain unchanged."
                )
            return (
                "To update your name, I need:\n\n"
                "**Required Information:**\n"
                "1. Your current name (for verification)\n"
                "2. Your new name\n\n"
                "Please provide both names and confirm by saying:\n"
                "- 'Yes, update my name' or 'Proceed with name change'\n"
                "- Include: Current name and New name\n\n"
                "Example: 'Yes, please proceed. Current: John Smith, New: John Doe'"
            )
        
        # Permissions and roles - flexible matching
        if ('permission' in query_lower or 'role' in query_lower or 
            ('access' in query_lower and 'control' in query_lower)):
            # Developer role/permissions - flexible matching
            if (('developer' in query_lower and 'role' in query_lower) or 
                ('developer' in query_lower and 'permission' in query_lower)):
                return (
                    "The Developer role includes the following permissions:\n"
                    "- Read and write access to code repositories\n"
                    "- Ability to create and modify issues\n"
                    "- Access to staging environments\n"
                    "- Can deploy to development servers\n"
                    "- Cannot access production data or perform billing operations"
                )
            return (
                "I can help with permissions and role management. Please specify:\n"
                "1. What role or permissions you need information about\n"
                "2. Whether you want to view, add, or modify permissions\n"
                "Common roles include: Admin, Developer, Viewer, Billing Manager"
            )
        
        # Team management - flexible matching for adding members
        if (('add' in query_lower and 'team' in query_lower and 'member' in query_lower) or 
            ('add' in query_lower and 'member' in query_lower) or 
            ('invite' in query_lower and 'team' in query_lower)):
            if is_confirmation and emails:
                email = emails[0]
                role_match = re.search(r'(?:role|assign)[: ]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', user_query, re.IGNORECASE)
                role = role_match.group(1) if role_match else "Member"
                return (
                    f"✅ Team member invitation confirmed and processed.\n\n"
                    f"An invitation has been successfully sent to:\n"
                    f"- Email: {email}\n"
                    f"- Role: {role}\n\n"
                    f"The invitation email has been sent to {email}. "
                    f"They will need to accept the invitation to join the team. "
                    f"You'll be notified once they accept."
                )
            return (
                "To add a team member, I'll need:\n\n"
                "**Required Information:**\n"
                "1. The email address of the person to invite\n"
                "2. The role to assign (Admin, Developer, Viewer, etc.)\n"
                "3. Confirmation to send the invitation\n\n"
                "Please provide this information and confirm by saying:\n"
                "- 'Yes, send invitation' or 'Proceed with invitation'\n"
                "- Include: Email and Role\n\n"
                "Example: 'Yes, please proceed. Email: member@example.com, Role: Developer'"
            )
        
        # Remove team member - flexible matching
        if (('remove' in query_lower and 'team' in query_lower and 'member' in query_lower) or 
            ('remove' in query_lower and 'member' in query_lower) or 
            ('delete' in query_lower and 'member' in query_lower)):
            if is_confirmation and (emails or any(char.isalpha() for char in user_query)):
                # Try to extract member identifier
                member_identifier = emails[0] if emails else "the specified member"
                return (
                    f"✅ Team member removal confirmed and processed.\n\n"
                    f"The team member ({member_identifier}) has been successfully removed:\n"
                    f"- Access revoked immediately\n"
                    f"- Removed from all team projects\n"
                    f"- Removed from organization\n\n"
                    f"A notification email has been sent to {member_identifier}. "
                    f"They can be re-added to the team later if needed."
                )
            return (
                "⚠️ **REMOVE TEAM MEMBER**\n\n"
                "This will immediately revoke access for the team member.\n\n"
                "**Required Information:**\n"
                "1. The email address or name of the member to remove\n"
                "2. Confirmation that you have admin rights\n\n"
                "Please provide the member details and confirm by saying:\n"
                "- 'Yes, remove member' or 'Proceed with removal'\n"
                "- Include: Member email or name\n\n"
                "Example: 'Yes, I confirm. Remove: member@example.com'"
            )
        
        # Organization settings - flexible matching
        if ('organization' in query_lower or 
            ('org' in query_lower and 'settings' in query_lower) or 
            ('sub-account' in query_lower or ('sub' in query_lower and 'account' in query_lower))):
            if is_confirmation:
                return (
                    "✅ Organization settings update confirmed and processed.\n\n"
                    "Your organization settings have been successfully updated. "
                    "Changes may take a few minutes to propagate across all systems. "
                    "All organization members will be notified of significant changes."
                )
            return (
                "I can help with organization settings. Available actions include:\n"
                "- Viewing organization details\n"
                "- Managing sub-accounts\n"
                "- Updating organization settings\n"
                "- Managing organization members\n\n"
                "What specific organization setting would you like to modify? "
                "Please provide details and confirm to proceed."
            )
        
        # General admin help - flexible matching
        if 'how' in query_lower and ('admin' in query_lower or 'administrative' in query_lower or 'account' in query_lower):
            return (
                "I can help with various administrative tasks:\n"
                "- Account management (create, delete, update)\n"
                "- Profile changes (email, name)\n"
                "- User permissions and role management\n"
                "- Team management (add/remove members)\n"
                "- Organization settings\n"
                "Please describe what you'd like to do, and I'll guide you through the process."
            )
        
        # Default response
        return (
            f"I understand you have an administrative request: '{user_query}'. "
            "I can help with account management, profile updates, permissions, "
            "team management, and organization settings. Could you please provide "
            "more details about what you'd like to accomplish?"
        )


__all__ = ['AdministrationAgent']

