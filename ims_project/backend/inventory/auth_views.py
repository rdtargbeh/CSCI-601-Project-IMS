# from django.contrib.auth import authenticate
# from django.contrib.auth.models import User
# from rest_framework.authtoken.models import Token
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from django.http import JsonResponse

# # ✅ Login View
# @api_view(["POST"])
# @permission_classes([AllowAny])  # Allow anyone to access
# def login_user(request):
#     """Authenticate user and return token"""
#     username = request.data.get("username")
#     password = request.data.get("password")
#     user = authenticate(username=username, password=password)

#     if user:
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({"token": token.key, "username": user.username})
#     return Response({"error": "Invalid credentials"}, status=400)

# # ✅ Logout View
# @api_view(["POST"])
# def logout_user(request):
#     """Logout user by deleting token"""
#     request.user.auth_token.delete()
#     return Response({"message": "Logged out successfully!"})

# # ✅ User Profile View
# @api_view(["GET"])
# def get_user_profile(request):
#     """Retrieve authenticated user profile"""
#     user = request.user
#     return Response({
#         "username": user.username,
#         "email": user.email,
#         "full_name": user.get_full_name(),
#     })
