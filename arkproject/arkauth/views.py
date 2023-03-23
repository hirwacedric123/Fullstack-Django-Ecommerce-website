from django.shortcuts import render, HttpResponse,redirect
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

#to activate user account
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.urls import NoReverseMatch,reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,force_str,DjangoUnicodeDecodeError


# Getting token from utils.py
from .utils import TokenGenerator,generate_token

# for emails
from django.core.mail import send_mail,EmailMultiAlternatives
from django.core.mail import BadHeaderError,send_mail
from django.core import mail
from django.conf import settings
from django.core.mail import EmailMessage
#reset passowrd generators

from django.contrib.auth.tokens import PasswordResetTokenGenerator

#THREADING
import threading

# Create your views here.

class EmailThread(threading.Thread):
    def __init__(self,email_message):
        self.email_message=email_message
        threading.Thread.__init__(self)
    def run(self):
        self.email_message.send()


def signup(request):
    
    if request.method=="POST":
        email=request.POST.get('email')
        get_password=request.POST.get('pass1')
        get_confirm_password=request.POST.get('pass2')
        if get_password!=get_confirm_password:
            messages.info(request,'Password is not matching')
            return redirect('auth/signup.html')
        
        try:
            if User.objects.get(username=email):
                messages.warning(request,"Email is already Taken")
                return redirect('auth/signup.html')
        except Exception as identifier:
            pass
        user=User.objects.create_user(email,email,get_password)
        user.is_active = False
        
        user.save()
        current_site=get_current_site(request)
        email_subject="Activate Your Account"
        message=render_to_string('auth/activate.html', { 
            'user':user,
            'domain':'127.0.0.1:8000',
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':generate_token.make_token(user)
        })
        email_message=EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email],)

        EmailThread(email_message).start()
        messages.info(request, "Activate Your Account by Clicking on Link sent on Your Email")
        return redirect('/arkauth/login')
        
    return render(request,'auth/signup.html')

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = str(urlsafe_base64_decode(uidb64), encoding='utf-8')
            user = User.objects.get(pk=uid)
        except ValueError:
            user = None

        if user is not None and generate_token.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()
                messages.info(request, "Account activated successfully.")
                return redirect('/arkauth/login')
            else:
                messages.warning(request, "Your account is already activated.")
            return redirect(reverse('/arkauth/login'))
        else:
            messages.error(request, "Activation link is invalid or has expired.")
            return render(request, 'auth/login.html')
# class ActivateAccountView(View):
#     def get(self,request,uidb64,token):
#         try:
#             uid=force_text(urlsafe_base64_decode(uidb64))
#             user=User.objects.get(pk=uid)
#         except Exception as identifier:
#             user=None
#         if user is not None and generate_token.check_token(user,token):
#             user.is_active=True
#             user.save()
#             messages.info(request,"Account is Activated Successful")
#             return redirect('/arkauth/login')
#         return render(request,'auth/login.html')    

def handlelogin(request):
    if request.method=="POST":
        email=request.POST.get('email')
        get_password=request.POST.get('pass1')
        myuser= authenticate(username=email,password=get_password)

        if myuser is not None:
            login(request,myuser)
            messages.success(request,"Login Success")
            return render(request,'index.html')
        else:
            messages.error(request,"Invalid Credentials")
            return redirect('/arkauth/login')
    return render(request,'auth/login.html')  
def handlelogout(request):
    logout(request)
    messages.success(request,'logout success')
    return redirect('/arkauth/login')

class RequestResetEmailView(View):
    def get(self,request):
        return render(request,'auth/request-reset-email.html')
    def post(self,request):
        email=request.POST['email']
        user=User.objects.filter(email=email)

        if user.exists():
            current_site=get_current_site(request)
            email_subject='[Reset Your Password]'
            message=render_to_string('auth/reset-user-password.html',
            {
                'domain':'127.0.0.1:8000',
                'uid':urlsafe_base64_encode(force_bytes(user[0].pk)),
                'token':PasswordResetTokenGenerator().make_token(user[0])
            })
            
            email_message=EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email])
            EmailThread(email_message).start()
            messages.info(request,"we have sent you email link to reset your Password")
            return render(request,'auth/request-reset-email.html')

class SetNewPasswordView(View):
    def get(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }
        try:
            user_id = str(urlsafe_base64_decode(uidb64), 'utf-8')
            user = User.objects.get(pk=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                messages.warning(request, "Password reset link is Invalid")
                return render(request, 'auth/request-reset-email.html')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist,
                DjangoUnicodeDecodeError):
            pass
        return render(request, 'auth/set-new-password.html', context)

    def post(self, request, uidb64, token):
        context = {
            'uidb64': uidb64,
            'token': token
        }
        get_password = request.POST.get('pass1')
        get_confirm_password = request.POST.get('pass2')

        if get_password != get_confirm_password:
            messages.info(request, 'Password is not matching')
            return redirect('auth/set-new-password.html', context)

        try:
            user_id = str(urlsafe_base64_decode(uidb64), 'utf-8')
            user = User.objects.get(pk=user_id)
            user.set_password(get_password)
            user.save()
            messages.success(request, "Password Reset Successful!! Login with your new password")
            return redirect('/arkauth/login/')

        except (TypeError, ValueError, OverflowError, User.DoesNotExist,
                DjangoUnicodeDecodeError):
            messages.error(request, "Something went wrong")
            return render(request, 'auth/set-new-password.html', context)

        return render(request, 'auth/set-new-password.html', context)

# class SetNewPasswordView(View):
#     def get(self,request,uidb64,token):
#         context= {
#             'uidb64':uidb64,
#             'token':token
#         }
#         try:
#             user_id=force_text(urlsafe_base64_decode(uidb64))
#             user=User.objects.get(pk=user_id)

#             if not PasswordResetTokenGenerator().check_token(user,token):
#                 messages.warning(request,"Password reset link is Invalid")
#                 return render(request,'auth/request-reset-email.html')
#         except DjangoUnicodeDecodeError as identifier:
#             pass
#         return render(request,'auth/set-new-password.html',context)
   
    # def post(self,request,uidb64,token):
    #     context= {
    #     'uidb64':uidb64,
    #     'token':token
    #     }
    #     get_password=request.POST('pass1')
    #     get_confirm_password=request.POST('pass2')

    #     if get_password!=get_confirm_password:
    #         messages.info(request,'Password is not matching')
    #         return redirect('auth/set-new-password.html',context)

    #     try:
    #         user_id=force_text(urlsafe_base64_decode(uidb64))
    #         user=User.objects.get(pk=user_id)
    #         user.set_password(passowrd)
    #         user.save()
    #         messages.success(request,"Password Reset Sucessful!! login with your New Password")
    #         return redirect('/arkauth/login/')

    #     except DjangoUnicodeDecodeError as identifier:
    #         messages.error(request,"Something Went wrong")
    #         return render(request,'auth/set-new-password.html',context)
        
    #     return render(request,'auth/set-new-password.html',context)

