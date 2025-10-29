# app/core/constants.py
from fastapi import status
from types import MappingProxyType
from typing import Mapping

STATUS_MESSAGE: Mapping[str, str] = MappingProxyType({
    # 공통/에러
    "INTERNAL_SERVER_ERROR": "internal_server_error",
    "REQUIRED_AUTHORIZATION": "required_authorization",
    "INVALID_USER_ID": "invalid_user_id",
    "NOT_FOUND_USER": "not_found_user",
    "INVALID_PASSWORD": "invalid_password",
    "INVALID_CREDENTIALS": "invalid_credentials",
    "FAILED_TO_UPDATE_SESSION": "failed_to_update_session",
    "TOO_MANY_REQUESTS": "too_many_requests",

    # 인증/세션
    "LOGIN_SUCCESS": "login_success",
    "LOGOUT_SUCCESS": "logout_success",

    # 회원가입/유저
    "ALREADY_EXIST_EMAIL": "already_exist_email",
    "FAILED_TO_SIGNUP": "failed_to_signup",
    "SIGNUP_SUCCESS": "signup_success",
    "UPDATE_PROFILE_IMAGE_FAILED": "update_profile_image_failed",
    "UPDATE_USER_DATA_SUCCESS": "update_user_data_success",
    "CHANGE_PASSWORD_SUCCESS": "change_password_success",
    "DELETE_USER_DATA_SUCCESS": "delete_user_data_success",
    "CHANGE_USER_PASSWORD_SUCCESS": "change_user_password_success",

    # 닉네임/이메일 중복 체크
    "AVAILABLE_EMAIL": "available_email",
    "ALREADY_EXIST_NICKNAME": "already_exist_nickname",
    "AVAILABLE_NICKNAME": "available_nickname",

    # 유효성 검사
    "INVALID_EMAIL_FORMAT": "invalid_email_format",
    "INVALID_PASSWORD_FORMAT": "invalid_password_format",
    "INVALID_NICKNAME_FORMAT": "invalid_nickname_format",

    # 게시글 관련
    "INVALID_POST_TITLE": "invalid_post_title",
    "INVALID_POST_TITLE_LENGTH": "invalid_post_title_length",
    "INVALID_POST_CONTENT": "invalid_post_content",
    "INVALID_POST_CONTENT_LENGTH": "invalid_post_content_length",
    "DELETE_POST_FAILED": "delete_post_failed",

    "WRITE_POST_FAILED": "write_post_failed",
    "WRITE_POST_SUCCESS": "write_post_success",

    "GET_POST_LIST_FAILED": "get_post_list_failed",
    "GET_POST_LIST_SUCCESS": "get_post_list_success",
    "GET_POST_FAILED": "get_post_failed",
    "GET_POST_SUCCESS": "get_post_success",

    "NOT_FOUND_POST": "not_found_post",
    "NOT_A_SINGLE_POST": "not_a_single_post",

    "UPDATE_POST_SUCCESS": "update_post_success",
    "DELETE_POST_SUCCESS": "delete_post_success",
    "GET_POSTS_SUCCESS": "get_posts_success",
    "GET_POSTS_FAILED":  "get_posts_failed",
    "FILE_UPLOAD_SUCCESS": "file_upload_success",

    # 댓글 관련
    "GET_COMMENTS_SUCCESS": "get_comments_success",
    "GET_COMMENTS_FAILED": "get_comments_failed",
    "WRITE_COMMENT_SUCCESS": "write_comment_success",
    "WRITE_COMMENT_FAILED": "write_comment_failed",
    "UPDATE_COMMENT_SUCCESS": "update_comment_success",
    "UPDATE_COMMENT_FAILED": "update_comment_failed",
    "DELETE_COMMENT_SUCCESS": "delete_comment_success",
    "DELETE_COMMENT_FAILED": "delete_comment_failed",
    "REQUERED_AUTHORIZATION": "required_authorization",
})

STATUS_CODE: Mapping[str, int] = MappingProxyType({
    # 2xx
    "OK": status.HTTP_200_OK,
    "CREATED": status.HTTP_201_CREATED,
    "ACCEPTED": status.HTTP_202_ACCEPTED,
    "NO_CONTENT": status.HTTP_204_NO_CONTENT,
    "END": status.HTTP_204_NO_CONTENT,
    # 4xx
    "BAD_REQUEST": status.HTTP_400_BAD_REQUEST,
    "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
    "FORBIDDEN": status.HTTP_403_FORBIDDEN,
    "NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "CONFLICT": status.HTTP_409_CONFLICT,
    # 5xx
    "INTERNAL_SERVER_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "NOT_IMPLEMENTED": status.HTTP_501_NOT_IMPLEMENTED,
    "BAD_GATEWAY": status.HTTP_502_BAD_GATEWAY,
    "SERVICE_UNAVAILABLE": status.HTTP_503_SERVICE_UNAVAILABLE,
})