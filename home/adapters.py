from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import uuid
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter for handling account-related operations"""
    
    def save_user(self, request, user, form, commit=True):
        """Save user with custom fields"""
        user = super().save_user(request, user, form, commit=False)
        if not user.userID:
            user.userID = f"U{uuid.uuid4().hex[:8].upper()}"
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for handling social account login (Google)"""
    
    def pre_social_login(self, request, sociallogin):
        """
        Invoked before the social login completes.
        Check if user with same email exists and connect the social account.
        Also update user info from Google.
        """
        logger.info(f"pre_social_login called, is_existing: {sociallogin.is_existing}")
        
        extra_data = sociallogin.account.extra_data
        email = extra_data.get('email')
        
        # Update user info from Google for existing social login
        if sociallogin.is_existing:
            user = sociallogin.user
            self._update_user_from_google(user, extra_data)
            return
        
        # Check if user with this email exists
        try:
            logger.info(f"Checking for existing user with email: {email}")
            if email:
                try:
                    existing_user = User.objects.get(email=email)
                    logger.info(f"Found existing user: {existing_user.userID}")
                    
                    # Update user info from Google
                    self._update_user_from_google(existing_user, extra_data)
                    
                    # Connect the social account to existing user
                    sociallogin.connect(request, existing_user)
                except User.DoesNotExist:
                    logger.info("No existing user found with this email")
        except Exception as e:
            logger.error(f"Error in pre_social_login: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _update_user_from_google(self, user, extra_data):
        """Update user info from Google extra_data"""
        # Get name from Google
        given_name = extra_data.get('given_name', '')
        family_name = extra_data.get('family_name', '')
        full_name = extra_data.get('name', '')
        
        logger.info(f"Google data: given_name='{given_name}', family_name='{family_name}', name='{full_name}'")
        
        # For Vietnamese names, we want to show the last part of the name
        # Google usually returns: given_name="Phú", family_name="Nguyễn Quốc"
        # Or sometimes weird: given_name="31-Nguyễn", family_name="Quốc Phú"
        
        # Use full_name and take the last word as first_name
        if full_name:
            # Remove any prefix numbers like "31-"
            clean_name = full_name
            if '-' in clean_name.split()[0] if clean_name.split() else False:
                parts = clean_name.split('-', 1)
                if len(parts) > 1:
                    clean_name = parts[1]
            
            name_parts = clean_name.strip().split()
            if name_parts:
                user.first_name = name_parts[-1]  # Tên cuối (Phú)
                user.last_name = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''
        elif given_name:
            # Fallback to given_name
            user.first_name = given_name.split('-')[-1] if '-' in given_name else given_name
            user.last_name = family_name
        
        logger.info(f"Updated user: first_name='{user.first_name}', last_name='{user.last_name}'")
        user.save()

    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social account data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Generate unique userID for new users
        user.userID = f"G{uuid.uuid4().hex[:8].upper()}"
        
        # Set role as 'user' by default
        user.role = 'user'
        
        # Get additional data from Google
        extra_data = sociallogin.account.extra_data
        logger.info(f"Google extra_data: {extra_data}")
        
        # Get full name from Google
        full_name = extra_data.get('name', '')
        given_name = extra_data.get('given_name', '')
        family_name = extra_data.get('family_name', '')
        
        # For Vietnamese names, take the last word of full_name as first_name
        # E.g., "Nguyễn Quốc Phú" -> first_name="Phú", last_name="Nguyễn Quốc"
        if full_name:
            # Remove any prefix numbers like "31-"
            clean_name = full_name
            first_part = clean_name.split()[0] if clean_name.split() else ''
            if '-' in first_part:
                parts = clean_name.split('-', 1)
                if len(parts) > 1:
                    clean_name = parts[1].strip()
            
            name_parts = clean_name.split()
            if name_parts:
                user.first_name = name_parts[-1]  # Tên cuối (Phú)
                user.last_name = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''
        elif given_name:
            # Fallback to given_name
            user.first_name = given_name.split('-')[-1] if '-' in given_name else given_name
            user.last_name = family_name
        
        # Set username from email if not set
        if not user.username:
            email = extra_data.get('email', '')
            user.username = email.split('@')[0] if email else f"user_{uuid.uuid4().hex[:6]}"
        
        logger.info(f"Populated user: first_name={user.first_name}, last_name={user.last_name}, username={user.username}")
        
        # Set profile picture URL (optional - you can download and save it)
        # if 'picture' in extra_data:
        #     user.photo_url = extra_data.get('picture')
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Save the user after social authentication
        """
        try:
            user = sociallogin.user
            logger.info(f"Saving social user: {user.email}")
            
            # Ensure userID is set before saving (it's the primary key)
            if not user.userID:
                user.userID = f"G{uuid.uuid4().hex[:8].upper()}"
            
            logger.info(f"UserID: {user.userID}")
            
            # Ensure role is set
            if not user.role:
                user.role = 'user'
                
            # Save user
            user.save()
            logger.info(f"User saved successfully: {user.userID}")
            
            # Connect social account
            sociallogin.save(request)
            logger.info(f"Social login saved for user: {user.userID}")
            
            return user
        except Exception as e:
            logger.error(f"Error saving social user: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
