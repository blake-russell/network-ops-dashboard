from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

def maintenance_mode(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        #return HttpResponse("This page is currently under maintenance.", status=503)
        return render(request, "network_ops_dashboard/maintenance_mode.html", status=503)
    return _wrapped_view