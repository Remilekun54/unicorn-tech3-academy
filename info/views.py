from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from info.models import Course, Comment


# Home Page View
class HomeView(View):
    def get(self, request):
        return render(request, 'info/home.html')


# About Page View
class AboutView(View):
    def get(self, request):
        return render(request, 'info/about.html')


# FAQ View
class FaqsView(View):
    def get(self, request):
        return render(request, 'info/faqs.html')


# FAQ View
class InstructorsView(View):
    def get(self, request):
        return render(request, 'info/instructors.html')


# Pricing View
class PricingView(View):
    def get(self, request):
        return render(request, 'info/pricing.html')


# Testimonial View
class TestimonialsView(View):
    def get(self, request):
        return render(request, 'info/testimonials.html')


# Services View
class ServicesView(View):
    def get(self, request):
        return render(request, 'info/services.html')


# Contact Page View
class ContactView(View):
    def get(self, request):
        return render(request, 'info/contact.html')

    def post(self, request):
        name = request.POST.get('name')
        email = request.POST.get('email')
        website = request.POST.get('website')
        message = request.POST.get('comments')

        # Add a simple validation check
        if not name or not email or not message:
            messages.error(request, 'All fields are required.')
            return render(request, 'info/contact.html')

        Comment.objects.create(name=name, email=email, webite=website, message=message)

        # we can display a success message
        messages.success(request, 'Thank you for contacting us. We will get back to you soon.')
        return render(request, 'info/contact.html')


# Course List View
class CourseListView(View):
    def get(self, request):
        # Fetch all available courses
        courses = Course.objects.all()  # Fetch all courses
        paginator = Paginator(courses, 10)  # Display 10 courses per page

        page_number = request.GET.get('page')  # Get the current page number
        page_obj = paginator.get_page(page_number)  # Fetch the corresponding page
        return render(request, 'info/course_list.html', {'page_obj': page_obj})


class CourseDetailsView(View):
    def get(self, request, course_id):
        # Fetch the course by ID or return a 404 if it doesn't exist
        course = get_object_or_404(Course, id=course_id)

        # Fetch all lessons associated with the course
        lessons = course.lessons.all()

        # Fetch the last 4 courses
        course_list = Course.objects.order_by('-id')[:4]

        return render(request, 'info/course_single.html', {
            'course': course,
            'course_list': course_list,
            'lessons': lessons,
            'student_no': 20,
        })


class PaymentDetailsView(View):
    def get(self, request, course_id):
        # Fetch the course by ID or return a 404 if it doesn't exist
        course = get_object_or_404(Course, id=course_id)

        return render(request, 'info/course_payment.html', {
            'course': course,
        })
