from django.contrib import admin

from .models import Course, Lesson, Comment

# Course Admin
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'created_at')
    search_fields = ('title',)
    ordering = ('created_at',)


admin.site.register(Course, CourseAdmin)


# Course Material Admin
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'duration', 'is_completed', 'created_at')
    list_filter = ('course', 'created_at', 'is_completed')
    search_fields = ('title', 'course__title')


admin.site.register(Lesson, LessonAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'created_at')
    list_filter = ('created_at',)


admin.site.register(Comment, CommentAdmin)
