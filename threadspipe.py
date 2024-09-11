import requests, base64, time, logging, re, math, filetype, string, random, datetime, webbrowser
import urllib.parse as urlp
from  typing import Optional, List, Any


from dotenv import set_key

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

class ThreadsPipe:
    __threads_media_post_endpoint__ = ""
    __threads_post_publish_endpoint__ = ""
    __threads_rate_limit_endpoint__ = ""
    __threads_post_reply_endpoint__ = ""
    __threads_profile_endpoint__ = ""
    __threads_access_token_endpoint__ = "https://graph.threads.net/oauth/access_token"
    __threads_access_token_refresh_endpoint__ = "https://graph.threads.net/refresh_access_token"

    __threads_post_length_limit__ = 500
    __threads_media_limit__ = 10

    __threads_rate_limit__ = 250
    __threads_reply_rate_limit__ = 1000

    __threads_access_token__ = ''
    __threads_user_id__ = ''

    __wait_before_post_publish__ = True
    __post_publish_wait_time__ = 30

    __wait_before_media_item_publish__ = True
    __media_item_publish_wait_time__ = 10

    __handle_hashtags__ = True
    __auto_handle_hashtags__ = False

    __gh_bearer_token__ = None
    __gh_api_version__ = "2022-11-28"
    __gh_username__ = None
    __gh_repo_name__ = None
    __gh_upload_timeout__ = 60 * 5

    __wait_on_rate_limit__ = False
    __check_rate_limit_before_post__ = True

    __handled_media__ = []

    __threads_auth_scope__ = {
        'basic': 'threads_basic', 
        'publish': 'threads_content_publish', 
        'read_replies': 'threads_read_replies', 
        'manage_replies': 'threads_manage_replies', 
        'insights': 'threads_manage_insights'
    }
    threads_post_insight_metrics = ['views', 'likes', 'replies', 'reposts', 'quotes']
    threads_user_insight_metrics = ["views", "likes", "replies", "reposts", "quotes", "followers_count", "follower_demographics"]
    threads_follower_demographic_breakdown_list = ['country', 'city', 'age', 'gender']
    who_can_reply_list = ['everyone', 'accounts_you_follow', 'mentioned_only']

    def __init__(
            self, 
            user_id: int, 
            access_token: str, 
            disable_logging = False,
            wait_before_post_publish = True,
            post_publish_wait_time = 35, # 30 seconds wait time before publishing a post
            wait_before_media_item_publish = True,
            media_item_publish_wait_time = 10, # 30 seconds wait time before publishing a post
            handle_hashtags = True,
            auto_handle_hashtags = False,
            gh_bearer_token = None,
            gh_api_version = "2022-11-28",
            gh_repo_name = None,
            gh_username = None,
            gh_upload_timeout = 60 * 5,
            wait_on_rate_limit = False,
            check_rate_limit_before_post = True
        ) -> None:

        self.__threads_access_token__ = access_token
        self.__threads_user_id__ = user_id

        self.__wait_before_post_publish__ = wait_before_post_publish
        self.__post_publish_wait_time__ = post_publish_wait_time

        self.__wait_before_media_item_publish__ = wait_before_media_item_publish
        self.__media_item_publish_wait_time__ = media_item_publish_wait_time

        self.__threads_media_post_endpoint__ = f"https://graph.threads.net/v1.0/{user_id}/threads?access_token={access_token}"
        self.__threads_post_publish_endpoint__ = f"https://graph.threads.net/v1.0/{user_id}/threads_publish?access_token={access_token}"
        self.__threads_rate_limit_endpoint__ = f"https://graph.threads.net/v1.0/{user_id}/threads_publishing_limit?access_token={access_token}"
        self.__threads_post_reply_endpoint__ = f"https://graph.threads.net/v1.0/me/threads?access_token={access_token}"
        self.__threads_profile_endpoint__ = f"https://graph.threads.net/v1.0/me?access_token={access_token}"

        self.__handle_hashtags__ = handle_hashtags

        self.__auto_handle_hashtags__ = auto_handle_hashtags

        self.__gh_bearer_token__ = gh_bearer_token
        self.__gh_api_version__ = gh_api_version
        self.__gh_username__ = gh_username
        self.__gh_repo_name__ = gh_repo_name
        self.__gh_upload_timeout__ = gh_upload_timeout

        self.__wait_on_rate_limit__ = wait_on_rate_limit
        self.__check_rate_limit_before_post__ = check_rate_limit_before_post

        if disable_logging:
            logging.disable()


    def pipe(
            self, 
            post: Optional[str] = "", 
            files: Optional[List] = [], 
            file_captions: List[str | None] = [],
            tags: Optional[List] = [],
            reply_to_id: Optional[str] = None, 
            who_can_reply: str | None = None,
            chained_post = True, 
            persist_tags_multipost = False,
            allowed_country_codes: str | List[str] = None,
        ):

        if len(files) == 0 and (post is None or post == ""):
                raise Exception("Either text or at least 1 media (image or video) or both must be provided")
        
        tags = tags

        # who_can_reply: everyone | accounts_you_follow | mentioned_only

        _post = post

        if allowed_country_codes is not None:
            is_eligible_for_geo_gating = self.is_eligible_for_geo_gating()
            if 'error' in is_eligible_for_geo_gating:
                return is_eligible_for_geo_gating
            elif is_eligible_for_geo_gating['is_eligible_for_geo_gating'] == False:
                return self.__tp_response_msg__(
                    message="You are attempting to send a geo-gated content but you are not eligible for geo-gating",
                    body=is_eligible_for_geo_gating,
                    is_error=True
                )


        if post != None and (self.__handle_hashtags__ or self.__auto_handle_hashtags__):
            extract_tags_reg = re.compile(r"(?<=\s)(#[\w\d]+(?:\s#[\w\d]+)*)$")
            extract_tags = extract_tags_reg.findall(post)[0].split(' ')
            tags = tags if len(extract_tags) == 0 else extract_tags
            _post = _post if len(extract_tags) == 0 else extract_tags_reg.sub('', _post).strip()

        splitted_post = self.__split_post__(_post, tags)

        print("files", len(files))

        _captions = [file_captions[x] if x < len(file_captions) else None for x in range(len(files))]

        files = self.__handle_media__(files)
        if 'error' in files:
            return files
        splitted_files = [files[self.__threads_media_limit__ * x: self.__threads_media_limit__ * (x + 1)] for x in range(math.ceil(len(files)/self.__threads_media_limit__))]

        splitted_captions = [_captions[self.__threads_media_limit__ * x: self.__threads_media_limit__ * (x + 1)] for x in range(math.ceil(len(files)/self.__threads_media_limit__))]

        print("files:", files)

        allowed_country_codes = allowed_country_codes if type(allowed_country_codes) is str else None if allowed_country_codes is None else ",".join(allowed_country_codes)


        media_ids = []
        prev_post_chain_id = reply_to_id
        for s_post in splitted_post:
            prev_post_chain_id = self.__send_post__(
                s_post, 
                medias=[] if splitted_post.index(s_post) >= len(splitted_files) else splitted_files[splitted_post.index(s_post)],
                media_captions=[] if splitted_post.index(s_post) >= len(splitted_captions) else splitted_captions[splitted_post.index(s_post)],
                reply_to_id=None if prev_post_chain_id is None else prev_post_chain_id['id'],
                allowed_listed_country_codes=allowed_country_codes,
                who_can_reply=who_can_reply
            )
            if 'error' in prev_post_chain_id:
                return prev_post_chain_id
            else:
                media_ids.append(prev_post_chain_id['id'])
        
        print("done sending posts", len(splitted_post))
        
        if len(splitted_files) > len(splitted_post):
            for file in splitted_files[len(splitted_post):]:
                prev_post_chain_id = self.__send_post__(
                    None, 
                    medias=file,
                    media_captions=[] if splitted_post.index(s_post) >= len(splitted_captions) else splitted_captions[splitted_post.index(s_post)],
                    reply_to_id=None if prev_post_chain_id is None else prev_post_chain_id['id'],
                    allowed_listed_country_codes=allowed_country_codes,
                    who_can_reply=who_can_reply
                )
                if 'error' in prev_post_chain_id:
                    return prev_post_chain_id
                else:
                    media_ids.append(prev_post_chain_id['id'])

        print("deleting files")
        self.__delete_uploaded_files__(files=files)
        logging.info("All posts piped to Instagram Threads successfully!")
        return self.__tp_response_msg__(
            message='All posts piped to Instagram Threads successfully!',
            is_error=False,
            body={'media_ids': media_ids}
        )

        
    def get_quota_usage(self, silent=True, for_reply=False):
        field = "&fields=reply_quota_usage,reply_config" if for_reply == True else "&fields=quota_usage,config"
        req_rate_limit = requests.get(self.__threads_rate_limit_endpoint__ + field)
            
        if 'data' in req_rate_limit.json():
            return req_rate_limit.json()
        else:
            return None
        
    def get_auth_token(self, app_id: str, redirect_uri: str, scope: str | List[str] = 'all', state: str | None = None):
        scope = [x for x in self.__threads_auth_scope__.values()] if type(scope) == str and scope == 'all' else [self.__threads_auth_scope__[x] for x in scope]
        scope = ','.join(scope)
        state = f"&state={state}" if state is not None else ""
        url = f'https://threads.net/oauth/authorize/?client_id={app_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}{state}'
        webbrowser.open(url)

    def get_access_token(self, app_id: str, app_secret: str, auth_code: str, redirect_uri: str):
        req_short_lived_access_token = requests.post(
            self.__threads_access_token_endpoint__,
            json={
                'client_id': app_id,
                'client_secret': app_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
        )

        short_lived_token = req_short_lived_access_token.json()

        print('short_lived_token', req_short_lived_access_token.status_code, short_lived_token)

        if req_short_lived_access_token.status_code > 201:
            return {
                "message": "Could not generate short lived token",
                "error": short_lived_token
            }

        req_long_lived_access_token = requests.get(
            f"https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={app_secret}&access_token={short_lived_token['access_token']}"
        )

        if req_long_lived_access_token.status_code > 201:
            return {
                "message": "Could not generate long lived token",
                "error": req_long_lived_access_token.json()
            }

        return {
            'user_id': short_lived_token['user_id'],
            'tokens': {
                'short_lived': short_lived_token,
                'long_lived': req_long_lived_access_token.json(),
            }
        }
    
    def refresh_token(self, access_token: str, env_path: str = None, env_variable: str = None):
        refresh_token_url = self.__threads_access_token_refresh_endpoint__ + f"?grant_type=th_refresh_token&access_token={access_token}"
        refresh_token = requests.get(refresh_token_url)
        if refresh_token.status_code > 201:
            return {
                'message': "An error occured could not refresh access token",
                'error': refresh_token.json()
            }
        if env_path != None and env_variable != None:
            set_key(env_path, env_variable, refresh_token['access_token'])
        return refresh_token.json()
    
    def is_eligible_for_geo_gating(self):
        url = self.__threads_profile_endpoint__ + "&fields=id,is_eligible_for_geo_gating"
        send_request = requests.get(url)
        if send_request.status_code != 200:
            logging.error(f"Could not get geo gating eligibility from Threads, Error:: {send_request.json()}")
            return self.__tp_response_msg__(
                message="Could not get geogating eligibility from Threads",
                body=send_request.json(),
                is_error=True
            )
        return send_request.json()
    
    def get_allowlisted_country_codes(self, limit: str | int = None):
        ret_limit = "" if limit == None else "&limit=" + str(limit)
        url = self.__threads_post_reply_endpoint__ + f"&fields=id,allowlisted_country_codes{ret_limit}"
        request_list = requests.get(url)
        return request_list.json()

    def get_posts(self, since_date: str | None = None, until_date: str | None = None, limit: str | int | None = None):
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"
        _limit = "" if limit is None else f"&limit={str(limit)}"
        url = self.__threads_post_reply_endpoint__ + f"&fields=id,media_product_type,media_type,media_url,permalink,owner,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post{since}{until}{_limit}"
        req_posts = requests.get(url)
        return req_posts.json()
    
    def get_post(self, post_id: str):
        url = f"https://graph.threads.net/v1.0/{post_id}?fields=id,media_product_type,media_type,media_url,permalink,owner,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post&access_token={self.__threads_access_token__}"
        req_post = requests.get(url)
        return req_post.json()
    
    def get_profile(self):
        url = self.__threads_profile_endpoint__ + f"&fields=id,username,name,threads_profile_picture_url,threads_biography"
        req_profile = requests.get(url)
        return req_profile.json()

    def get_post_replies(self, post_id: str, top_levels=True, reverse=False):
        _reverse = "false" if reverse is False else "true"
        reply_level_type = "replies" if top_levels is True else "conversation"
        url = f"https://graph.threads.net/v1.0/{post_id}/{reply_level_type}?fields=id,text,timestamp,media_product_type,media_type,media_url,shortcode,thumbnail_url,children,has_replies,root_post,replied_to,is_reply,hide_status&reverse={_reverse}&access_token={self.__threads_access_token__}"
        req_replies = requests.get(url)
        return req_replies.json()
    
    def get_user_replies(self, since_date: str | None = None, until_date: str | None = None, limit: int | str = None):
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"
        _limit = "" if limit is None else f"&limit={str(limit)}"
        url = f"https://graph.threads.net/v1.0/me/replies?fields=id,media_product_type,media_type,media_url,permalink,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post,has_replies,root_post,replied_to,is_reply,is_reply_owned_by_me,reply_audience&since={since}&until={until}&limit={_limit}&access_token={self.__threads_access_token__}"
        req_replies = requests.get(url)
        return req_replies.json()
    
    def hide_reply(self, reply_id: str, hide: bool):
        _hide = "true" if hide is True else "false"
        url = f"https://graph.threads.net/v1.0/{reply_id}/manage_reply"
        req_hide_reply = requests.post(
            url,
            data={
                "access_token":self.__threads_access_token__,
                "hide": _hide
            }
        )
        return req_hide_reply.json()
    
    def get_post_insight(self, post_id: str, metrics: str | List[str] = 'all'):
        _metric = ",".join(self.threads_post_insight_metrics) if metrics == 'all' else metrics
        _metric = ','.join(_metric) if type(_metric) is list else _metric
        _metric = "&metric=" + _metric
        url = f"https://graph.threads.net/v1.0/{post_id}/insights?access_token={self.__threads_access_token__}{_metric}"
        req_insight = requests.get(url)
        return req_insight.json()
    
    def get_user_insight(self, user_id: str | None = None, since_date: str | None = None, until_date: str | None = None, follower_demographic_breakdown: str = 'country', metrics: str | List[str] = 'all'):
        _metric = ",".join(self.threads_user_insight_metrics) if metrics == 'all' else metrics
        _metric = ','.join(_metric) if type(_metric) is list else _metric
        _metric = "&metric=" + _metric
        _demographic_break_down = "&breakdown=" + follower_demographic_breakdown
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"

        _user_id = user_id if user_id is not None else "me"

        url = f"https://graph.threads.net/v1.0/{_user_id}/threads_insights?access_token={self.__threads_access_token__}{_metric}{since}{until}{_demographic_break_down}"
        req_insight = requests.get(url)
        return req_insight.json()
    
    def get_post_intent(self, text: str = None, link: str = None):
        _text = "" if text is None else self.__quote_str__(text)
        _url = "" if link is None else "&url=" + urlp.quote(link,safe="")
        return f"https://www.threads.net/intent/post?text={_text}{_url}"
    
    def get_follow_intent(self, username: str | None = None):
        _username = username if username is not None else self.get_profile()['username']
        return f"https://www.threads.net/intent/follow?username={_username}"


    def __send_post__(
            self, 
            post: str = None, 
            medias: Optional[List] = [], 
            media_captions: List[str | None] = [],
            reply_to_id: Optional[str] = None,
            allowed_listed_country_codes: str | None = None,
            who_can_reply: str | None = None
        ):
        is_carousel = len(medias) > 1
        media_cont = medias

        if self.__check_rate_limit_before_post__ or self.__wait_on_rate_limit__ == True:
            quota = self.get_quota_usage() if reply_to_id is None else self.get_quota_usage(for_reply=True)
            if quota is not None:
                quota_usage = quota['data'][0]['quota_usage'] if reply_to_id is None else quota['data'][0]['reply_quota_usage']
                quota_duration = quota['data'][0]['config']['quota_duration'] if reply_to_id is None else quota['data'][0]['reply_config']['quota_duration']
                limit = quota['data'][0]['config']['quota_total'] if reply_to_id is None else quota['data'][0]['reply_config']['quota_total']
                if quota_usage > limit and self.__wait_on_rate_limit__ == True:
                    time.sleep(quota_duration)
                elif quota_usage > limit:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    logging.error("Rate limit exceeded!")
                    return self.__tp_response_msg__(
                        message='Rate limit exceeded!', 
                        body=quota,
                        is_error=True
                    )
                

        MEDIA_CONTAINER_ID = ''
        post_text = f"&text={self.__quote_str__(post)}" if post is not None else ""
        allowed_countries = f"&allowlisted_country_codes={allowed_listed_country_codes}" if allowed_listed_country_codes is not None else ""
        reply_control = "" if who_can_reply is None else f"&reply_control={who_can_reply}"

        if is_carousel:
            MEDIA_CONTAINER_IDS_ARR = []
            for media in media_cont:
                media_query = "image_url=" + media['url'].replace('&', '%26') if media['type'] == 'IMAGE' else "video_url=" + media['url'].replace('&', '%26')
                caption = None if media_cont.index(media) > len(media_captions) else media_captions[media_cont.index(media)]
                caption = None if caption is None else {"alt_text": caption}
                carousel_post_url = f"{self.__threads_media_post_endpoint__}&media_type={media['type']}&is_carousel_item=true&{media_query}{allowed_countries}"
                req_post = requests.post(carousel_post_url, json=caption)
                if req_post.status_code > 201:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    logging.error(f"An error occured while creating an item container or a uploading media file at index {media_cont.index(media)}, Error:: {req_post.json()}")
                    return self.__tp_response_msg__(
                        message=f"An error occured while creating an item container or a uploading media file at index {media_cont.index(media)}", 
                        body=req_post.json(),
                        is_error=True
                    )

                logging.info(f"Media/file at index {media_cont.index(media)} uploaded {req_post.json()}")

                media_debug = self.__debug_post__(req_post.json()['id'])
                f_info = f"\n::Note:: waiting for the upload status of the media item/file at index {media_cont.index(media)} to be 'FINISHED'" if media_debug['status'] != "FINISHED" else ''
                logging.info(f"Media upload debug for media/file at index {media_cont.index(media)}:: {media_debug}{f_info}")
                while media_debug['status'] != "FINISHED":
                    time.sleep(self.__post_publish_wait_time__)
                    media_debug = self.__debug_post__(req_post.json()['id'])
                    f_info = f"\n::Note:: waiting for the upload status of the media item/file at index {media_cont.index(media)} to be 'FINISHED'" if media_debug['status'] != "FINISHED" else ''
                    logging.info(f"Media upload debug for media/file at index {media_cont.index(media)}:: {media_debug}{f_info}")
                    if media_debug['status'] == 'ERROR':
                        self.__delete_uploaded_files__(files=self.__handled_media__)
                        logging.error(f"Media item / file at index {media_cont.index(media)} could not be published, Error:: {media_debug}")
                        return self.__tp_response_msg__(
                            message=f"Media item / file at index {media_cont.index(media)} could not be published", 
                            body=media_debug,
                            is_error=True
                        )

                MEDIA_CONTAINER_IDS_ARR.append(req_post.json()['id'])
                
            
            media_ids_str = ",".join(MEDIA_CONTAINER_IDS_ARR)
            endpoint = self.__threads_post_reply_endpoint__ if reply_to_id is not None else self.__threads_media_post_endpoint__
            reply_to_id = "" if reply_to_id is None else f"&reply_to_id={reply_to_id}"
            carousel_cont_url = f"{endpoint}&media_type=CAROUSEL&children={media_ids_str}{post_text}{reply_to_id}{allowed_countries}{reply_control}"

            req_create_carousel = requests.post(carousel_cont_url)
            if req_create_carousel.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                logging.error(f"An error occured while creating media carousel, Error:: {req_create_carousel.json()}")
                return self.__tp_response_msg__(
                    message="An error occured while creating media carousel or a post with multiple files", 
                    body=req_create_carousel.json(),
                    is_error=True
                )
            
            MEDIA_CONTAINER_ID = req_create_carousel.json()['id']
            
        else:
            media_type = "TEXT" if len(medias) == 0 else media_cont[0]['type']
            media = "" if len(medias) == 0 else media_cont[0]['url'].replace('&', '%26')
            media_url = "&image_url=" + media if media_type == "IMAGE" else "&video_url=" + media
            media_url = "" if len(medias) == 0 else media_url

            endpoint = self.__threads_post_reply_endpoint__ if reply_to_id is not None else self.__threads_media_post_endpoint__
            reply_to_id = "" if reply_to_id is None else f"&reply_to_id={reply_to_id}"
            # caption = "" if len(media_captions) == 0 else media_captions[0]
            # caption = "" if caption is None else "&alt_text=" + caption
            caption = None if len(media_captions) == 0 else media_captions[0]
            caption = None if caption is None else {"alt_text": caption}
            make_post_url = f"{endpoint}&media_type={media_type}{media_url}{post_text}{reply_to_id}{allowed_countries}{reply_control}"
            request_endpoint = requests.post(make_post_url, json=caption)
            
            if request_endpoint.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                logging.error(f"An error occured while creating media, Error:: {request_endpoint.json()}")
                return self.__tp_response_msg__(
                    message="An error occured while creating media / single post blueprint", 
                    body=request_endpoint.json(),
                    is_error=True
                )

            print("request_endpoint.json()", request_endpoint.status_code, request_endpoint.json())
            MEDIA_CONTAINER_ID = request_endpoint.json()['id']

        delete_gh_files = True
        try:
            post_debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            d_info = '\n::Note:: waiting for the post\'s ready status to be \'FINISHED\'' if post_debug['status'] != 'FINISHED' else ''
            logging.info(f"Post publish-ready status:: {post_debug}{d_info}")

            while post_debug['status'] != 'FINISHED':
                time.sleep(self.__post_publish_wait_time__)
                post_debug = self.__debug_post__(MEDIA_CONTAINER_ID)
                d_info = '\n::Note:: waiting for the post\'s ready status to be \'FINISHED\'' if post_debug['status'] != 'FINISHED' else ''
                logging.info(f"Post publish-ready status:: {post_debug}{post_debug}{d_info}")
                if post_debug['status'] == 'ERROR':
                    logging.error(f"Uploaded media could not be published, Error:: {post_debug}")
                    return self.__tp_response_msg__(
                        message="Uploaded media could not be published", 
                        body=post_debug,
                        is_error=True
                    )

            publish_post_url = f"{self.__threads_post_publish_endpoint__}&creation_id={MEDIA_CONTAINER_ID}{allowed_countries}"
            publish_post = requests.post(publish_post_url)
            if publish_post.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                delete_gh_files = False
                logging.error(f"Could not publish post, Error:: {publish_post.json()}")
                return self.__tp_response_msg__(
                    message=f"Could not publish post", 
                    body=publish_post.json(),
                    is_error=True
                )

            print("publish_post", publish_post.json())
            post_debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            if post_debug['status'] != 'PUBLISHED':
                self.__delete_uploaded_files__(files=self.__handled_media__)
                delete_gh_files = False
                logging.error(f"Post not sent, Error message {post_debug['error_message']}")
                return self.__tp_response_msg__(
                    message=f"Post not sent, Error message {post_debug['error_message']}", 
                    body=post_debug,
                    is_error=True
                )
            # return publish_post.json()['id']
            return {'id': publish_post.json()['id']}
        
        except Exception as e:
            debug = {}
            if delete_gh_files:
                self.__delete_uploaded_files__(files=self.__handled_media__)  

            if len(medias) > 0:
                debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            
            logging.error(f"Could not send post")
            logging.error(f"Exception: {e}")
            if len(debug.keys()) > 0:
                logging.error(f"Published Post Debug: {debug}")

            # sys.exit()  
            return self.__tp_response_msg__(
                message=f"An unknown error occured could not send post", 
                body=debug | {'e': e},
                is_error=True
            )
    
    def __debug_post__(self, media_id: int):
        media_debug_endpoint = f"https://graph.threads.net/v1.0/{media_id}?fields=status,error_message&access_token={self.__threads_access_token__}"
        req_debug_response = requests.get(media_debug_endpoint)
        return req_debug_response.json()
    
    def __split_post__(self, post: str, tags: List) -> List[str]:
        if len(post) <= self.__threads_post_length_limit__:
            first_tag = "" if len(tags) == 0 else "\n"+tags[0].strip()
            first_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post) else first_tag
            return [post + first_tag]
        
        tagged_post = []
        untagged_post = []

        clip_tags = tags[:math.ceil(len(post) / self.__threads_post_length_limit__)]

        prev_strip = 0
        for i in range(len(clip_tags)):
            _tag = "\n"+clip_tags[i].strip()
            extra_strip = 3 if i == 0 else 6
            prev_tag = len("\n"+clip_tags[i - 1].strip()) + extra_strip if i > 0 else len("\n"+clip_tags[i].strip()) + extra_strip
            pre_dots = "" if i == 0 else "..."
            sub_dots = "..." if i + 1 < len(clip_tags) else ""
            put_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post[(self.__threads_post_length_limit__ * i) : (self.__threads_post_length_limit__ * (i+1))]) else _tag
            start_strip = prev_tag
            _post = pre_dots + post[(self.__threads_post_length_limit__ * i) - prev_strip : (self.__threads_post_length_limit__ * (i + 1)) - (extra_strip + prev_strip + len(put_tag))] + sub_dots + put_tag
            prev_strip = (extra_strip + prev_strip + len(put_tag))
            tagged_post.append(_post)
        
        has_more_text = len(''.join(tagged_post)) < len(post)

        extra_text = post[len(''.join(tagged_post)):]

        if has_more_text:
            text_split_range = math.ceil(len(extra_text)/self.__threads_post_length_limit__)
            start_strip = 0
            for i in range(text_split_range):
                extra_strip = 3 if i == 0 and len(tagged_post) == 0 else 6
                pre_dots = "" if i == 0 and len(tagged_post) == 0 else "..."
                sub_dots = "..." if i + 1 < text_split_range else ""
                _post = pre_dots + post[(self.__threads_post_length_limit__ * i) - start_strip : (self.__threads_post_length_limit__ * (i + 1)) - (extra_strip + start_strip)] + sub_dots
                start_strip = (extra_strip + start_strip)
                untagged_post.append(_post)

        print("type", type(tagged_post + untagged_post))

        return tagged_post + untagged_post
        

    def __should_handle_hash_tags__ (self, post: None | str):
        if post == None:
            return False
        return len(re.compile(r"([\w\s]+)?(\#\w+)\s?\w+").findall(post)) == 0 if self.__auto_handle_hashtags__ == True else self.__handle_hashtags__

    @staticmethod
    def __quote_str__(text):
        return urlp.quote(text)
    
    @staticmethod
    def __rand_str__(length):
        characters = string.ascii_letters + string.digits  # You can add more characters if desired
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string
    
    @staticmethod
    def __is_base64__(o_str):
        if not o_str or len(o_str) % 4 != 0:
            return False

        base64_regex = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')

        if not base64_regex.match(o_str):
            return False

        try: # check by attempting to decode it
            base64.b64decode(o_str, validate=True)
            return True
        except (base64.binascii.Error, ValueError):
            return False
    
    def __handle_media__(self, media_files: List[Any]):
        for file in media_files:
            url_file_reg = re.compile(r"^(https?:\/\/)?([a-zA-Z0-9]+\.)?[a-zA-Z0-9]+\.[a-zA-Z0-9]{2,}(\/.*)?$")
            if type(file) == str and url_file_reg.match(file):
                has_ext_reg = re.compile(r"\.(?P<ext>[a-zA-Z0-9]+)$").search(file)
                media_type = None
                if has_ext_reg != None:
                    media_type = filetype.get_type(ext=has_ext_reg.group('ext'))
                    media_type = None if media_type is None else media_type.mime
                
                if has_ext_reg is None or media_type is None:
                    req_check_type = requests.head(file)
                    if req_check_type.status_code > 200:
                        self.__delete_uploaded_files__(files=self.__handled_media__)
                        logging.error(f"File at index {media_files.index(file)} could not be found so its type could not be determined")
                        return self.__tp_response_msg__(
                            message=f"File at index {media_files.index(file)} could not be found so its type could not be determined", 
                            body={},
                            is_error=True
                        )
                    media_type = req_check_type.headers['Content-Type']

                print("media_type", media_type)
                if media_type == None:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    logging.error(f"Filetype of the file at index {media_files.index(file)} is invalid")
                    return self.__tp_response_msg__(
                        message=f"Filetype of the file at index {media_files.index(file)} is invalid", 
                        body={},
                        is_error=True
                    )

                media_type = media_type.split('/')[0].upper()

                if media_type not in ['VIDEO', 'IMAGE']:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    logging.error(f"Provided file at index {media_files.index(file)} must be either an image or video file, {media_type} given")
                    return self.__tp_response_msg__(
                        message=f"Provided file at index {media_files.index(file)} must be either an image or video file, {media_type} given", 
                        body={},
                        is_error=True
                    )
                
                self.__handled_media__.append({ 'type': media_type, 'url': file })
                continue
            elif self.__is_base64__(file):
                _file = self.__get_file_url__(base64.b64decode(file), media_files.index(file))
                if 'error' in _file:
                    return _file
                self.__handled_media__.append(_file)
            else:
                _file = self.__get_file_url__(file, media_files.index(file))
                if 'error' in _file:
                    return _file
                self.__handled_media__.append(_file)

        return self.__handled_media__
    
    def __get_file_url__(self, file, file_index: int):
        if self.__gh_bearer_token__ == None or self.__gh_username__ == None or self.__gh_repo_name__ == None:
            logging.error(f"To handle local file uploads to threads please provide your GitHub fine-grained access token, your GitHub username and the name of your GitHub repository to be used for the temporary file upload")
            return self.__tp_response_msg__(
                message=f"To handle local file uploads to threads please provide your GitHub fine-grained access token, your GitHub username and the name of your GitHub repository to be used for the temporary file upload", 
                body={},
                is_error=True
            )
        
        if not filetype.is_image(file) and not filetype.is_video(file):
            self.__delete_uploaded_files__(files=self.__handled_media__)
            logging.error(f"Provided file at index {file_index} must be either an image or video file, {filetype.guess_mime(file)} given")
            return self.__tp_response_msg__(
                message=f"Provided file at index {file_index} must be either an image or video file, {filetype.guess_mime(file)} given", 
                body={},
                is_error=True
            )
        
        f_type = "IMAGE" if filetype.is_image(file) else "VIDEO"

        file_obj = {
            'type': f_type,
        }

        try:
            _f_type = filetype.guess(file).mime
            print("Uploading index", file_index, ", mime type", _f_type)
            file = open(file, 'rb').read() if type(file) == str else file
            
            filename = self.__rand_str__(10) + '.' + _f_type.split('/')[-1].lower()
            cur_time = datetime.datetime.today().ctime()
            req_upload_file = requests.put(
                f"https://api.github.com/repos/{self.__gh_username__}/{self.__gh_repo_name__}/contents/{filename}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.__gh_bearer_token__}",
                    "X-GitHub-Api-Version": self.__gh_api_version__
                },
                json={
                    "message": f"ThreadsPipe: At {cur_time}, Uploaded a file to be uploaded to threads for a post",
                    "content": base64.b64encode(file).decode('utf-8')
                },
                timeout=self.__gh_upload_timeout__,
                
            )
            req_upload_file.raise_for_status()
            response = req_upload_file.json()
            file_obj['url'] = response['content']['download_url']
            file_obj['sha'] = response['content']['sha']
            file_obj['_link'] = response['content']['_links']['self']

            print("response", response['content']['download_url'], response['content']['sha'])

        except Exception as e:
            self.__delete_uploaded_files__(files=self.__handled_media__)
            logging.error(f"An unknown error occured while trying to upload local file at index {file_index} to GitHub, error: {e}")
            return self.__tp_response_msg__(
                message=f"An unknown error occured while trying to upload local file at index {file_index} to GitHub", 
                body={'e': e},
                is_error=True
            )

        return file_obj
    
    def __delete_uploaded_files__(self, files: List[dict]):
        for file in files:
            try:
                if 'sha' in file:
                    cur_time = datetime.datetime.today().ctime()
                    req_upload_file = requests.delete(
                        file['_link'],
                        headers={
                            "Accept": "application/vnd.github+json",
                            "Authorization": f"Bearer {self.__gh_bearer_token__}",
                            "X-GitHub-Api-Version": self.__gh_api_version__
                        },
                        json={
                            "message": f"ThreadsPipe: At {cur_time}, Deleted a temporary uploaded file",
                            "sha": file['sha']
                        },
                        timeout=self.__gh_upload_timeout__
                    )
                    if req_upload_file.status_code != 200:
                        logging.warning(f"File at index {files.index(file)} was not deleted from GitHub due to an unknown error, status_code::", req_upload_file.status_code)
            except Exception as e:
                logging.error(f"The delete status of the file at index {files.index(file)} from the GitHub repository could not be determined, Error::", e)
    
    @staticmethod
    def __tp_response_msg__(message: str, body: Any, is_error: bool = False):
        return {'info': 'error', 'error': body | { 'message': message }} if is_error else {'info': 'success', 'data': body | { 'message': message }}
    
# t = ThreadsPipe()

