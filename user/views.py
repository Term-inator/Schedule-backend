import asyncio
import json
import os
import secrets

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from google_auth_oauthlib.flow import Flow
from django.shortcuts import redirect
from django.core.cache import cache
from django.http import HttpResponse

from main.decorators import errorHandler, checkToken
from main.settings import BASE_DIR
from main.consumer import send_message_to_user
from . import service
from .models import ScheduleUser


# Create your views here.
def googleLogin(request):
    uid = request.GET.get('uid')
    cache.set(uid, 0, 60 * 10)  # 保存 10 分钟
    print('googleLogin', uid)
    # 创建 Flow 实例
    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'user/client_secret.json'),
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri='http://127.0.0.1:8000/user/googleCallback/',
    )

    # 构造认证 URL 并重定向
    authorization_url, state = flow.authorization_url()
    request.session['state'] = state
    request.session['uid'] = uid

    return redirect(authorization_url)


def googleCallback(request):
    state = request.session['state']
    uid = request.session['uid']

    flow = Flow.from_client_secrets_file(
        os.path.join(BASE_DIR, 'user/client_secret.json'),
        scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email',
                'https://www.googleapis.com/auth/userinfo.profile'],
        state=state,
        redirect_uri='http://127.0.0.1:8000/user/googleCallback/'
    )

    # 使用返回的授权码获取令牌
    flow.fetch_token(authorization_response=request.get_full_path())

    if not flow.credentials:
        return HttpResponse(status=401)

    # 获取用户信息
    session = flow.authorized_session()
    profile_info = session.get('https://www.googleapis.com/userinfo/v2/me').json()

    # 在这里你可以根据 profile_info 创建或更新你的用户
    user, created = ScheduleUser.objects.get_or_create(
        email=profile_info['email'],
        defaults={
            'first_name': profile_info['given_name'],
            'last_name': profile_info['family_name'],
            'profile_image_url': profile_info['picture'],
            'locale': profile_info['locale'],
        })

    token = secrets.token_hex(16)
    cache.set(token, user.id, 60 * 60 * 24 * 7)  # 保存 7 天

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            send_message_to_user(
                uid,
                {
                    'api': 'login',
                    'data': {
                        'token': token,
                        'id': user.id
                    }
                }
            ))
    finally:
        loop.close()
        asyncio.set_event_loop(None)  # 重置事件循环

    return HttpResponse(status=200)


@errorHandler
@checkToken
@require_http_methods(["POST"])
def getProfile(request, userId):
    return service.getProfileById(userId)