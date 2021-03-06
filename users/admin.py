import os
import csv
import datetime
import mimetypes

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.contrib.auth.admin import UserAdmin
from django.utils.encoding import smart_str
from wsgiref.util import FileWrapper
from django.http import HttpResponse, HttpResponseRedirect

from users.models import *


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'location', 'is_staff']
    search_fields = ['username', 'email']
    actions = ['export_users', 'send_email_to_users', 'send_notification_to_users']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(CustomUserAdmin, self).get_search_results(request, queryset, search_term)

        queryset |= self.model.objects.filter(info__city_name__icontains=search_term)
        queryset |= self.model.objects.filter(info__state_name__icontains=search_term)
        queryset |= self.model.objects.filter(info__country_name__icontains=search_term)
        return queryset, use_distinct

    def location(self, obj):
        if obj.is_staff:
            return ''
        return "({}, {}, {})".format(obj.info.city_name.encode('utf-8'), obj.info.state_name.encode('utf-8'), 
            obj.info.country_name.encode('utf-8'))

    def export_users(self, request, queryset):
        result_csv_fields = [
            'username',
            'email',
            'city',
            'state',
            'country',
            'avatar',
            'facebook_url',
            'twitter_url',
            'instagram_url'
        ]

        path = settings.MEDIA_ROOT+datetime.datetime.now().strftime("/user_csv/users_%Y_%m_%d_%H_%M_%S")
        result = open(path, 'w')
        result_csv = csv.DictWriter(result, fieldnames=result_csv_fields)
        result_csv.writeheader()

        for user in queryset:
            try:
                userprofile = UserProfile.objects.get(user=user)
            except Exception, e:
                continue

            user_ = {}
            user_['username'] = user.username
            user_['email'] = user.email
            user_['city'] = userprofile.city_name
            user_['state'] = userprofile.state_name
            user_['country'] = userprofile.country_name
            user_['avatar'] = userprofile.avatar
            user_['facebook_url'] = userprofile.facebook_url
            user_['twitter_url'] = userprofile.twitter_url
            user_['instagram_url'] = userprofile.instagram_url
            result_csv.writerow(user_)

        result.close()
        msg = "{} user(s) successfully exported.".format(queryset.count())
        self.message_user(request, msg)

        wrapper = FileWrapper( open( path, "r" ) )
        content_type = mimetypes.guess_type( path )[0]

        response = HttpResponse(wrapper, content_type = content_type)
        response['Content-Length'] = os.path.getsize( path ) # not FileField instance
        response['Content-Disposition'] = 'attachment; filename=%s/' % smart_str( os.path.basename( path ) ) # same here        
        return response

    export_users.short_description = "Export users as CSV file"

    def send_email_to_users(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect("/broadcast_email/?ids=%s" % (",".join(selected)))

    send_email_to_users.short_description = "Send an Email to Users"

    def send_notification_to_users(modeladmin, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect("/broadcast_notification/?ids=%s" % (",".join(selected)))

    send_notification_to_users.short_description = "Send a Notification to Users"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(UserProfile)
admin.site.register(PushNotification)
admin.site.register(UserNotification)
admin.site.register(UserRate)
admin.site.register(UserReport)
admin.site.register(UserFeed)
admin.site.register(UserRequest)
admin.site.register(UserInfinityBan)
admin.site.register(ContactReq)
