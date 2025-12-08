from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .forms import BotConfigurationForm
from .models import BotConfiguration, FAQ, ChatSession, ChatMessage, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count # Import Count UserProfile
from django.db.models.functions import TruncMonth # Import date aggregation for charts
from django.contrib.auth.decorators import login_required, user_passes_test # Import login_required and staff check
from django.contrib.auth import authenticate, login, logout # Import authenticate, login, and logout
from django.contrib.auth.forms import UserCreationForm # Import UserCreationForm
from .forms import BotConfigurationForm, UserRegistrationForm, EmailAuthenticationForm # Import UserRegistrationForm and EmailAuthenticationForm
from .services import get_gemini_response # Import Gemini service
from django.contrib import messages # Import messages
import json
import uuid
from django.core.serializers.json import DjangoJSONEncoder # To handle datetime objects
from django.core.mail import send_mail
from django.conf import settings
from .captcha_utils import generate_captcha_text, generate_captcha_image
from django.http import HttpResponse

# Create your views here.

# Staff user check decorator helper
def is_staff_user(user):
    return user.is_authenticated and user.is_staff

def get_faq_answer(user_query):
    """Retrieve FAQ answer using keyword matching (fallback to question matching)"""
    user_query_lower = user_query.lower().strip()
    # 1. Keyword-based matching
    for faq in FAQ.objects.all():
        if any(kw in user_query_lower for kw in faq.get_keywords_list()):
            return faq.answer
    # 2. Fallback to original question matching
    try:
        return FAQ.objects.get(question__icontains=user_query).answer
    except FAQ.DoesNotExist:
        return None

@login_required
@user_passes_test(is_staff_user)
def dashboard_stats(request):
    """Return admin dashboard statistics as JSON"""
    try:
        total_users = User.objects.count()
        active_bots = BotConfiguration.objects.filter(is_active=True).count()
        total_chats = ChatSession.objects.count()
        total_messages = ChatMessage.objects.count()

        return JsonResponse({
            'total_users': total_users,
            'active_bots': active_bots,
            'total_chats': total_chats,
            'total_messages': total_messages
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch dashboard stats: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_staff_user)
def admin_dashboard_charts(request):
    """Return admin dashboard chart data as JSON"""
    try:
        # Get monthly user registrations (uses User model's date_joined field)
        monthly_registrations = User.objects\
            .annotate(month=TruncMonth('date_joined'))\
            .values('month')\
            .annotate(count=Count('id'))\
            .order_by('month')

        # Format month as readable string (e.g., "Jan 2025")
        formatted_registrations = [
            {
                'month': entry['month'].strftime('%b %Y'),
                'count': entry['count']
            }
            for entry in monthly_registrations
        ]

        return JsonResponse({
            'user_registrations': formatted_registrations
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to fetch chart data: {str(e)}'
        }, status=500)

def home(request):
    return render(request, 'chat/home.html')

def about(request):
    return render(request, 'chat/about.html')

def chat(request):
    print(f"Chat view called. Request method: {request.method}, User authenticated: {request.user.is_authenticated}")
    if not request.user.is_authenticated:
        print("User not authenticated, redirecting to login page.")
        return redirect('login')

    # Handle GET request - check for session ID
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        bots = BotConfiguration.objects.all() # Fetch all bot configurations

        if session_id:
            # Check if session exists and has messages
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                chat_session = ChatSession.objects.get(
                    user_profile=user_profile,
                    session_id=session_id
                )
                # Only allow access if session has messages
                if chat_session.messages.exists():
                    return render(request, 'chat/chat.html', {'session_id': session_id, 'bots': bots})
                else:
                    # Empty session, redirect to chat without session_id
                    return redirect('/chat/')
            except (UserProfile.DoesNotExist, ChatSession.DoesNotExist):
                # Session doesn't exist, redirect to chat without session_id
                return redirect('/chat/')
        else:
            # No session_id provided, show chat interface without creating session
            return render(request, 'chat/chat.html', {'session_id': None, 'bots': bots})

    # Handle POST request
    if request.method == 'POST':
        user_message = request.POST.get('message')
        session_id = request.POST.get('session_id')
        selected_bot_id = request.POST.get('bot_id') # Get selected bot ID

        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

        chat_session = None
        if session_id:
            # Try to get existing session for the current user
            try:
                chat_session = ChatSession.objects.get(
                    user_profile=user_profile,
                    session_id=session_id
                )
            except ChatSession.DoesNotExist:
                # If session_id is provided but doesn't exist for this user,
                # treat it as a new session request with a new ID.
                print(f"Provided session_id {session_id} not found for user {request.user.username}. Creating new session.")
                session_id = str(uuid.uuid4()) # Generate a new UUID
                chat_session = ChatSession.objects.create(
                    user_profile=user_profile,
                    session_id=session_id
                )
        
        if not chat_session: # If no session_id was provided or the provided one was invalid/not found
            session_id = str(uuid.uuid4())
            chat_session = ChatSession.objects.create(
                user_profile=user_profile,
                session_id=session_id
            )

        # Get the selected bot configuration
        selected_bot = None
        if selected_bot_id:
            try:
                selected_bot = BotConfiguration.objects.get(id=selected_bot_id)
            except BotConfiguration.DoesNotExist:
                pass # Handle case where bot doesn't exist

        # Save user message
        ChatMessage.objects.create(
            session=chat_session,
            sender='user',
            content=user_message
        )

        # Simple FAQ matching logic
        faq_match = FAQ.objects.filter(question__icontains=user_message).first()
        if faq_match:
            bot_response = faq_match.answer
            print(f"FAQ matched. Bot response: {bot_response}")
        else:
            try:
                # If no FAQ match, get response from Gemini
                bot_response = get_gemini_response(user_message, bot_config=selected_bot) # Pass bot_config
                print(f"Gemini response: {bot_response}")
            except Exception as e:
                # Handle potential errors from Gemini service
                print(f"Error getting response from AI: {e}")
                return JsonResponse({'error': f'Error getting response from AI: {str(e)}'}, status=500)

        # Save bot response (either from FAQ or Gemini)
        ChatMessage.objects.create(
            session=chat_session,
            sender='bot',
            content=bot_response
        )

        response_data = {'response': bot_response, 'session_id': session_id}
        print(f"Returning JSON response: {response_data}")
        return JsonResponse(response_data)
    print("Returning chat.html for GET request.")
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    # Filter out sessions that have no messages
    chat_sessions_queryset = ChatSession.objects.filter(user_profile=user_profile, messages__isnull=False).distinct().order_by('-start_time')

    # Serialize chat sessions and their messages
    serialized_chat_sessions = []
    for session in chat_sessions_queryset:
        messages = []
        for message in session.messages.all().order_by('timestamp'):
            messages.append({
                'text': message.content,
                'isUser': message.sender == 'user',
                'time': message.timestamp.strftime("%I:%M %p") # Format time for display
            })
        serialized_chat_sessions.append({
            'session_id': str(session.session_id),
            'messages': messages
        })

    initial_chat_sessions_json = json.dumps(serialized_chat_sessions, cls=DjangoJSONEncoder)

    bots = BotConfiguration.objects.all() # Fetch all bot configurations for GET request
    context = {
        'initial_chat_sessions_json': initial_chat_sessions_json,
        'bots': bots # Pass bots to the template
    }
    return render(request, 'chat/chat.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        description = request.POST.get('description')
        owner_email = 'patelgargi2305@gmail.com'  # Change this to the real owner email

        mail_subject = f'Contact Form Submission from {name}'
        mail_message = (
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Description: {description}\n"
        )
        send_mail(
            subject=mail_subject,
            message=mail_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
            recipient_list=[owner_email],
            fail_silently=False,
        )
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
    return render(request, 'chat/contact.html')

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST) # Use EmailAuthenticationForm
        print(f"Login attempt: Form is valid: {form.is_valid()}") # Debug print
        if form.is_valid():
            user = form.get_user() # Get the authenticated user from the form
            print(f"User authenticated: {user}") # Debug print
            if user is not None:
                login(request, user)
                print("User successfully logged in. Checking for next_url...") # Debug print
                next_url = request.GET.get('next')
                print(f"next_url: {next_url}") # New debug print
                if next_url:
                    print(f"Redirecting to next_url: {next_url}") # Debug print
                    return redirect(next_url)
                else:
                    print(f"request.user.is_staff: {request.user.is_staff}") # New debug print
                    if request.user.is_staff:
                        print("Redirecting staff user to admin_dashboard") # Debug print
                        return redirect('admin_dashboard') # Redirect to admin dashboard after login
                    else:
                        print("Redirecting non-staff user to chat page with new_chat flag") # Debug print
                        from django.urls import reverse
                        return redirect(reverse('chat') + '?new_chat=true') # Redirect to chat page with new_chat flag
            else:
                print("Authentication failed: Invalid email or password.") # Debug print
                return render(request, 'chat/login.html', {'form': form, 'error_message': 'Invalid email or password.'})
        else:
            print(f"Form is not valid. Errors: {form.errors}") # Debug print
    else:
        form = EmailAuthenticationForm(request=request) # Use EmailAuthenticationForm for GET requests
    return render(request, 'chat/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in immediately after registration
            messages.success(request, 'Registration successful! You are now logged in.') # Add a success message
            # Redirect to user dashboard after successful registration
            return redirect('user_dashboard')
        else:
            # If form is not valid, check for specific errors like email already exists
            if 'email' in form.errors and 'user with this email already exists.' in form.errors['email']:
                messages.error(request, 'A user with this email already exists. Please log in.')
                return redirect('login')
            else:
                # Add a general error message for other form validation failures
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm(request=request)
    return render(request, 'chat/register.html', {'form': form})

@login_required
def user_dashboard(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    recent_chats = ChatSession.objects.filter(user_profile=user_profile).order_by('-start_time')[:5]  # Get 5 recent chats

    if request.method == 'POST':
        # Handle bot preference updates
        user_profile.bot_personality = request.POST.get('bot_personality', user_profile.bot_personality)
        user_profile.response_speed = request.POST.get('response_speed', user_profile.response_speed)
        user_profile.dark_mode = 'dark_mode' in request.POST  # Checkbox
        user_profile.save()
        messages.success(request, 'Bot preferences updated successfully!')
        return redirect('user_dashboard')

    # Calculate statistics for dashboard cards
    # 1. Total chats initiated
    total_chats = ChatSession.objects.filter(user_profile=user_profile).count()
    
    # 2. Total chat time (in hours)
    from django.db.models import Sum, F, ExpressionWrapper, DurationField
    from datetime import timedelta
    
    total_chat_time = ChatSession.objects.filter(
        user_profile=user_profile,
        end_time__isnull=False
    ).aggregate(
        total_time=Sum(F('end_time') - F('start_time'))
    )['total_time'] or timedelta()
    
    # Convert to hours with 1 decimal place
    total_hours = round(total_chat_time.total_seconds() / 3600, 1)
    
    # 3. Custom bots - counting all bot configurations since there's no user association in the model
    # TODO: Consider adding a user field to BotConfiguration for proper user isolation
    custom_bots = BotConfiguration.objects.count()

    # Fetch recent chats and get the first message of each
    recent_chats_with_first_message = []
    for chat_session in recent_chats:
        first_message = chat_session.messages.filter(sender='user').order_by('timestamp').first()
        recent_chats_with_first_message.append({
            'session_id': chat_session.session_id,
            'start_time': chat_session.start_time,
            'first_message_content': first_message.content if first_message else 'No messages yet.'
        })

    context = {
        'user_profile': user_profile,
        'recent_chats': recent_chats_with_first_message,
        'total_chats': total_chats,
        'total_chat_hours': total_hours,
        'custom_bots_count': custom_bots,
    }
    return render(request, 'chat/user_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('home')

    # Get total number of users (excluding superusers)
    total_users = UserProfile.objects.count()

    # Get total number of bot configurations
    active_bots = BotConfiguration.objects.count()

    # Get total number of chat sessions
    total_chats = ChatSession.objects.count()

    # Get total number of messages
    total_messages = ChatMessage.objects.count()

    context = {
        'total_users': total_users,
        'active_bots': active_bots,
        'total_chats': total_chats,
        'total_messages': total_messages,
    }

    return render(request, 'chat/admin_dashboard.html', context)

@login_required
def admin_dashboard_api(request):
    """API endpoint for admin dashboard analytics data"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from django.db.models import Count
    from django.db.models.functions import TruncMonth, TruncDay
    from django.utils import timezone
    import datetime

    # User registrations over time (last 12 months)
    user_registrations = User.objects.annotate(month=TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month')
    user_data = [{'month': entry['month'].strftime('%b %Y'), 'count': entry['count']} for entry in user_registrations]

    # Chat sessions over time (last 30 days)
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    chat_sessions = ChatSession.objects.filter(start_time__gte=thirty_days_ago).annotate(day=TruncDay('start_time')).values('day').annotate(count=Count('id')).order_by('day')
    chat_data = [{'day': entry['day'].strftime('%d %b'), 'count': entry['count']} for entry in chat_sessions]

    # Messages over time (last 30 days)
    messages = ChatMessage.objects.filter(timestamp__gte=thirty_days_ago).annotate(day=TruncDay('timestamp')).values('day').annotate(count=Count('id')).order_by('day')
    message_data = [{'day': entry['day'].strftime('%d %b'), 'count': entry['count']} for entry in messages]

    return JsonResponse({
        'user_registrations': user_data,
        'chat_sessions': chat_data,
        'messages': message_data,
    })


from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_history(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        ChatMessage.objects.filter(session__user_profile=user_profile).delete()
        ChatSession.objects.filter(user_profile=user_profile).delete()
        return JsonResponse({'success': True, 'message': 'Chat history deleted successfully.'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User profile not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def captcha_image(request):
    captcha_text = generate_captcha_text()
    request.session['captcha_text'] = captcha_text
    image_data = generate_captcha_image(captcha_text)
    return HttpResponse(image_data, content_type='image/png')

@login_required
def get_user_chat_sessions(request):
    """API endpoint to fetch all user-specific chat sessions and messages"""
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        chat_sessions = ChatSession.objects.filter(user_profile=user_profile, messages__isnull=False).distinct().order_by('-start_time')
        
        # Serialize sessions and messages (matches frontend format)
        serialized_sessions = []
        for session in chat_sessions:
            messages = []
            for msg in session.messages.all().order_by('timestamp'):
                messages.append({
                    'text': msg.content,
                    'isUser': msg.sender == 'user',
                    'time': msg.timestamp.strftime("%I:%M %p")
                })
            serialized_sessions.append({
                'session_id': str(session.session_id),
                'messages': messages
            })
        
        return JsonResponse({'success': True, 'sessions': serialized_sessions})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

from django.contrib import messages
from django.core.exceptions import PermissionDenied

@login_required
def bot_config_manage(request):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")

    bot_configurations = BotConfiguration.objects.all().order_by('-created_at')

    if request.method == 'POST':
        if 'delete_bot' in request.POST:
            # Handle bot deletion
            bot_id = request.POST.get('bot_id')
            try:
                bot = BotConfiguration.objects.get(id=bot_id)
                bot.delete()
                messages.success(request, 'Bot configuration deleted successfully!')
            except BotConfiguration.DoesNotExist:
                messages.error(request, 'Bot configuration not found.')
            return redirect('bot_config_manage')

        # Handle form submission for create/update
        bot_id = request.POST.get('bot_id')
        if bot_id:  # Edit existing bot
            bot = get_object_or_404(BotConfiguration, id=bot_id)
            form = BotConfigurationForm(request.POST, request.FILES, instance=bot)
            if form.is_valid():
                form.save()
                messages.success(request, 'Bot configuration updated successfully!')
                return redirect('bot_config_manage')
        else:  # Create new bot
            form = BotConfigurationForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, 'Bot configuration created successfully!')
                return redirect('bot_config_manage')
    else:
        form = BotConfigurationForm()

    context = {
        'form': form,
        'bots': bot_configurations,
        'active_bots': bot_configurations.count(),
    }
    return render(request, 'chat/bot_config_manage.html', context)

def faq_training(request):
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        if question and answer:
            FAQ.objects.create(question=question, answer=answer)
            return redirect('faq_training')
    faqs = FAQ.objects.all()
    return render(request, 'chat/faq_training.html', {'faqs': faqs})

def edit_faq(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if request.method == 'POST':
        question = request.POST.get('question')
        answer = request.POST.get('answer')
        if question and answer:
            faq.question = question
            faq.answer = answer
            faq.save()
            return redirect('faq_training')
    return render(request, 'chat/edit_faq.html', {'faq': faq})

def delete_faq(request, pk):
    faq = get_object_or_404(FAQ, pk=pk)
    if request.method == 'POST':
        faq.delete()
        return redirect('faq_training')

@login_required
def user_management(request):
    users = UserProfile.objects.annotate(session_count=Count('chat_sessions')).all() # Annotate with session count

    # Prepare data for chart
    user_labels = [user.user.username for user in users]
    session_counts = [user.session_count for user in users]

    context = {
        'users': users,
        'user_labels': user_labels,
        'session_counts': session_counts,
    }
    return render(request, 'chat/user_management.html', context)

@login_required
def user_chat_logs(request, user_id):
    user_profile = get_object_or_404(UserProfile, pk=user_id)
    chat_sessions = ChatSession.objects.filter(user_profile=user_profile).order_by('-start_time')

    context = {
        'user_profile': user_profile,
        'chat_sessions': chat_sessions,
    }
    return render(request, 'chat/user_chat_logs.html', context)

@login_required
def analytics(request):
    if not request.user.is_superuser:
        return redirect('home')

    return render(request, 'chat/analytics.html')

@login_required
def analytics_api(request):
    """API endpoint for comprehensive analytics data"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    from django.db.models import Count, Avg, Sum, F
    from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
    from django.utils import timezone
    import datetime

    # Time periods
    now = timezone.now()
    thirty_days_ago = now - datetime.timedelta(days=30)
    seven_days_ago = now - datetime.timedelta(days=7)

    # User analytics
    total_users = UserProfile.objects.count()
    active_users_30d = UserProfile.objects.filter(user__last_login__gte=thirty_days_ago).count()
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_users_7d = User.objects.filter(date_joined__gte=seven_days_ago).count()

    # Chat analytics
    total_sessions = ChatSession.objects.count()
    sessions_30d = ChatSession.objects.filter(start_time__gte=thirty_days_ago).count()
    sessions_7d = ChatSession.objects.filter(start_time__gte=seven_days_ago).count()
    total_messages = ChatMessage.objects.count()
    messages_30d = ChatMessage.objects.filter(timestamp__gte=thirty_days_ago).count()
    messages_7d = ChatMessage.objects.filter(timestamp__gte=seven_days_ago).count()

    # Average session duration (for sessions with end_time)
    avg_session_duration = ChatSession.objects.filter(end_time__isnull=False).aggregate(avg_duration=Avg(F('end_time') - F('start_time')))['avg_duration']
    if avg_session_duration:
        avg_session_duration = str(avg_session_duration).split('.')[0]  # Remove microseconds

    # Bot analytics
    total_bots = BotConfiguration.objects.count()
    faq_count = FAQ.objects.count()

    # Detailed time series data
    # User registrations by month (last 12 months)
    user_registrations = User.objects.annotate(month=TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month')
    user_data = [{'month': entry['month'].strftime('%b %Y'), 'count': entry['count']} for entry in user_registrations]

    # Daily active users (last 30 days)
    daily_active = User.objects.filter(last_login__gte=thirty_days_ago).annotate(day=TruncDay('last_login')).values('day').annotate(count=Count('id')).order_by('day')
    daily_data = [{'day': entry['day'].strftime('%d %b'), 'count': entry['count']} for entry in daily_active]

    # Chat sessions by day (last 30 days)
    chat_sessions_daily = ChatSession.objects.filter(start_time__gte=thirty_days_ago).annotate(day=TruncDay('start_time')).values('day').annotate(count=Count('id')).order_by('day')
    chat_daily_data = [{'day': entry['day'].strftime('%d %b'), 'count': entry['count']} for entry in chat_sessions_daily]

    # Messages by day (last 30 days)
    messages_daily = ChatMessage.objects.filter(timestamp__gte=thirty_days_ago).annotate(day=TruncDay('timestamp')).values('day').annotate(count=Count('id')).order_by('day')
    message_daily_data = [{'day': entry['day'].strftime('%d %b'), 'count': entry['count']} for entry in messages_daily]

    # User activity distribution
    user_activity = UserProfile.objects.annotate(session_count=Count('chat_sessions')).values('session_count').annotate(users=Count('id')).order_by('session_count')
    activity_data = [{'sessions': entry['session_count'], 'users': entry['users']} for entry in user_activity]

    return JsonResponse({
        'summary': {
            'total_users': total_users,
            'active_users_30d': active_users_30d,
            'new_users_30d': new_users_30d,
            'new_users_7d': new_users_7d,
            'total_sessions': total_sessions,
            'sessions_30d': sessions_30d,
            'sessions_7d': sessions_7d,
            'total_messages': total_messages,
            'messages_30d': messages_30d,
            'messages_7d': messages_7d,
            'avg_session_duration': avg_session_duration,
            'total_bots': total_bots,
            'faq_count': faq_count,
        },
        'charts': {
            'user_registrations': user_data,
            'daily_active_users': daily_data,
            'chat_sessions_daily': chat_daily_data,
            'messages_daily': message_daily_data,
            'user_activity': activity_data,
        }
    })
