from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .serializers import ContactUsSerializer,DemoScheduleSerializer

class ContactUsView(APIView):

    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            contact = serializer.save()

             # Send Email to Admin
            subject = "New Contact Us Submission"
            message = f"""
            New contact form submission:

            Name: {contact.name}
            Email: {contact.email}
            Mobile: {contact.phone}
            Message:
            {contact.message}
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],  # Admin email
                fail_silently=False,
            )
            return Response(
                {"message": "Contact form submitted successfully"},
                status=201
            )
        return Response(serializer.errors, status=400)
    
class ScheduleDemoView(APIView):

    def post(self, request):

        serializer = DemoScheduleSerializer(data=request.data)

        if serializer.is_valid():
            demo = serializer.save()

            #  Email to Admin
            send_mail(
                "New Demo Enquiry",
                f"""
New Demo Enquiry:

Name: {demo.full_name}
Email: {demo.email}
Phone: {demo.phone}
Course: {demo.course}
Message: {demo.message or "No message provided"}
""",
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],   # use settings
                fail_silently=False,
            )

            return Response(
                {"success": True, "message": "Demo enquiry submitted successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)