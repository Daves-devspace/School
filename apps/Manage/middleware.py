# # middleware.py
# from django.shortcuts import redirect
#
# class RoleBasedRedirectMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         if request.path == '/dashboard/' and request.user.is_authenticated:
#             user_role = request.user.role
#             if user_role == 'Admin':
#                 return redirect('director_dashboard')
#             elif user_role == 'teacher':
#                 return redirect('teacher-dashboard')
#             else:
#                 return redirect('student_dashboard')
#         return self.get_response(request)
#
#
#
# from django.urls import resolve
# #
# # class GroupRedirectMiddleware:
# #     def __init__(self, get_response):
# #         self.get_response = get_response
# #
# #     def __call__(self, request):
# #         # Paths to exclude from redirection
# #         excluded_paths = [
# #             '/home/',  # Replace with your Admin home path
# #             '/teacher-dashboard',
# #             '/director-dashboard'# Replace with your teacher dashboard path
# #             '/login',  # Replace with your login URL
# #             '/logout/',
# #             '/teacher-dashboard/login',# Replace with your logout URL
# #         ]
# #
# #         # Get the current request path
# #         current_path = request.path
# #
# #         # Check if the user is authenticated
# #         if request.user.is_authenticated and current_path not in excluded_paths:
# #             # Check group membership and redirect accordingly
# #             if request.user.groups.filter(name='Admin').exists():
# #                 return redirect('director_dashboard')  # Replace with your Admin home named URL
# #             elif request.user.groups.filter(name='Head Teacher').exists():
# #                 return redirect('teacher-dashboard')  # Replace with the Head Teacher dashboard URL
# #             elif request.user.groups.filter(name='Teacher').exists():
# #                 return redirect('teacher-dashboard')  # Replace with the Teacher dashboard URL
# #
# #         # Proceed with the normal request flow
# #         return self.get_response(request)
# #