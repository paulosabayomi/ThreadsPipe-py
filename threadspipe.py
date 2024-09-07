import requests, io, base64, time, logging, re, math, filetype, os, string, random, datetime, webbrowser
import urllib.parse as urlp
from  typing import Optional, List, Any


from dotenv import set_key

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

class ThreadsPipe:
    __threads_media_post_endpoint__ = ""
    __threads_post_publish_endpoint__ = ""
    __threads_rate_limit_endpoint__ = ""
    __threads_post_reply_endpoint__ = ""
    __threads_acces_token_endpoint__ = "https://graph.threads.net/oauth/access_token"
    __threads_acces_token_refresh_endpoint__ = "https://graph.threads.net/refresh_access_token"

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

    def __init__(
            self, 
            user_id: int, 
            access_token: str, 
            disable_logging = False,
            wait_before_post_publish = True,
            post_publish_wait_time = 30, # 30 seconds wait time before publishing a post
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
            tags: Optional[List] = [],
            reply_to_id: Optional[str] = None, 
            chained_post = True, 
            persist_tags_multipost = False
        ):

        if len(files) == 0 and (post is None or post == ""):
                raise Exception("Either text or at least 1 media (image or video) or both must be provided")
        
        tags = tags

        _post = post


        if post != None and (self.__handle_hashtags__ or self.__auto_handle_hashtags__):
            extract_tags_reg = re.compile(r"(?<=\s)(#[\w\d]+(?:\s#[\w\d]+)*)$")
            extract_tags = extract_tags_reg.findall(post)[0].split(' ')
            tags = tags if len(extract_tags) == 0 else extract_tags
            _post = _post if len(extract_tags) == 0 else extract_tags_reg.sub('', _post).strip()

        splitted_post = self.__split_post__(_post, tags)

        print("files", len(files))

        files = self.__handle_media__(files)
        splitted_files = [files[self.__threads_media_limit__ * x: self.__threads_media_limit__ * (x + 1)] for x in range(math.ceil(len(files)/self.__threads_media_limit__))]


        print("files:", files)


        prev_post_chain_id = reply_to_id
        for s_post in splitted_post:
            prev_post_chain_id = self.__send_post__(
                s_post, 
                medias=[] if splitted_post.index(s_post) >= len(splitted_files) else splitted_files[splitted_post.index(s_post)],
                reply_to_id=prev_post_chain_id
            )
        
        print("done sending posts", len(splitted_post))
        
        if len(splitted_files) > len(splitted_post):
            for file in splitted_files[len(splitted_post):]:
                prev_post_chain_id = self.__send_post__(
                    None, 
                    medias=file,
                    reply_to_id=prev_post_chain_id
                )

        print("deleting files")
        self.__delete_uploaded_files__(files=files)

        
    def get_quota_usage(self, silent=True, for_reply=False):
        field = "&fields=reply_quota_usage,reply_config" if for_reply == True else "&fields=quota_usage,config"
        req_rate_limit = requests.get(self.__threads_rate_limit_endpoint__ + field)

        if not silent:
            req_rate_limit.raise_for_status()
            
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
            self.__threads_acces_token_endpoint__,
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
                "msg": "Could not generate short lived token",
                "error": short_lived_token
            }

        req_long_lived_access_token = requests.get(
            f"https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={app_secret}&access_token={short_lived_token['access_token']}"
        )

        if req_long_lived_access_token.status_code > 201:
            return {
                "msg": "Could not generate long lived token",
                "error": req_long_lived_access_token.json()
            }

        return {
            'user_id': short_lived_token['user_id'],
            'tokens': {
                'short_lived': short_lived_token,
                'long_lived': req_long_lived_access_token.json(),
            }
        }
    
    def refresh_tokens(self, access_token: str, env_path: str = None, env_variable: str = None):
        refresh_token_url = self.__threads_acces_token_refresh_endpoint__ + f"?grant_type=th_refresh_token&access_token={access_token}"
        refresh_token = requests.get(refresh_token_url)
        if env_path != None and env_variable != None:
            set_key(env_path, env_variable, refresh_token['access_token'])
        return refresh_token.json()


    def __send_post__(self, post: str = None, medias: Optional[List] = [], reply_to_id: Optional[str] = None):
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
                    raise Exception("Rate limit exceeded!")

        MEDIA_CONTAINER_ID = ''
        post_text = f"&text={self.__quote_str__(post)}" if post is not None else ""

        if is_carousel:
            MEDIA_CONTAINER_IDS_ARR = []
            for media in media_cont:
                media_query = "image_url=" + media['url'] if media['type'] == 'IMAGE' else "video_url=" + media['url']
                carousel_post_url = f"{self.__threads_media_post_endpoint__}&media_type={media['type']}&is_carousel_item=true&{media_query}"
                req_post = requests.post(carousel_post_url)
                if req_post.status_code > 201:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    raise Exception(f"An error occured while creating an item container or uploading media file at index {media_cont.index(media)}, Error::", req_post.json())
                # req_post.raise_for_status()
                print("::::::::::uploaded media id", req_post.json())
                MEDIA_CONTAINER_IDS_ARR.append(req_post.json()['id'])
                
            
            media_ids_str = ",".join(MEDIA_CONTAINER_IDS_ARR)
            endpoint = self.__threads_post_reply_endpoint__ if reply_to_id is not None else self.__threads_media_post_endpoint__
            reply_to_id = "" if reply_to_id is None else f"&reply_to_id={reply_to_id}"
            carousel_cont_url = f"{endpoint}&media_type=CAROUSEL&children={media_ids_str}{post_text}{reply_to_id}"
            print("sleeping before posting...")
            # time.sleep(10)
            if self.__wait_before_media_item_publish__:
                time.sleep(self.__media_item_publish_wait_time__)
            req_create_carousel = requests.post(carousel_cont_url)
            # print("req_create_carousel", req_create_carousel.json())
            if req_create_carousel.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                raise Exception("An error occured while creating media carousel, Error::", req_create_carousel.json())
            
            # req_create_carousel.raise_for_status()
            MEDIA_CONTAINER_ID = req_create_carousel.json()['id']
            
        else:
            media_type = "TEXT" if len(medias) == 0 else media_cont[0]['type']
            media = "" if len(medias) == 0 else media_cont[0]['url']
            media_url = "&image_url=" + media if media_type == "IMAGE" else "&video_url=" + media
            media_url = "" if len(medias) == 0 else media_url
            endpoint = self.__threads_post_reply_endpoint__ if reply_to_id is not None else self.__threads_media_post_endpoint__
            reply_to_id = "" if reply_to_id is None else f"&reply_to_id={reply_to_id}"
            make_post_url = f"{endpoint}&media_type={media_type}{media_url}{post_text}{reply_to_id}"
            request_endpoint = requests.post(make_post_url)
            if request_endpoint.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                raise Exception("An error occured while creating media, Error::", request_endpoint.json())

            # request_endpoint.raise_for_status()
            MEDIA_CONTAINER_ID = request_endpoint.json()['id']

        try:
            if self.__wait_before_post_publish__:
                time.sleep(self.__post_publish_wait_time__)
            publish_post_url = f"{self.__threads_post_publish_endpoint__}&creation_id={MEDIA_CONTAINER_ID}"
            publish_post = requests.post(publish_post_url)
            if publish_post.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                raise Exception(f"Could not publish post, Error::", publish_post.json())

            post_debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            print(":::post_debug", post_debug, publish_post.json())
            if post_debug['status'] != 'PUBLISHED':
                self.__delete_uploaded_files__(files=self.__handled_media__)
                raise Exception(f"Post not sent, Error message {post_debug['error_message']}")
            return publish_post.json()['id']
        
        except Exception as e:
            debug = {}
            if len(medias) > 0:
                debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            
            logging.error(f"Could not send post")
            logging.error(f"Exception: {e}")
            if len(debug.keys()) > 0:
                logging.error(f"Published Post Debug: {debug['error_message']}")
            self.__delete_uploaded_files__(files=self.__handled_media__)            
    
    def __debug_post__(self, media_id: int):
        media_debug_endpoint = f"https://graph.threads.net/v1.0/{media_id}?fields=status,error_message&access_token={self.__threads_access_token__}"
        req_debug_response = requests.get(media_debug_endpoint)
        req_debug_response.raise_for_status()
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
            text_split_range = math.ceil(len(extra_text)/500)
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
                        raise Exception(f"File at index {media_files.index(file)} could not be found so its type could not be determined")
                    media_type = req_check_type.headers['Content-Type']

                print("media_type", media_type)
                if media_type == None:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    raise Exception(f"Filetype of the file at index {media_files.index(file)} is invalid")

                media_type = media_type.split('/')[0].upper()

                if media_type not in ['VIDEO', 'IMAGE']:
                    self.__delete_uploaded_files__(files=self.__handled_media__)
                    raise Exception(f"Provided file at index {media_files.index(file)} must be either an image or video file, {media_type} given")
                
                self.__handled_media__.append({ 'type': media_type, 'url': file })
                continue
            elif self.__is_base64__(file):
                self.__handled_media__.append(self.__get_file_url__(base64.b64decode(file), media_files.index(file)))
            else:
                self.__handled_media__.append(self.__get_file_url__(file, media_files.index(file)))

        return self.__handled_media__
    
    def __get_file_url__(self, file, file_index: int):
        # print("__gh_bearer_token__", self.__gh_bearer_token__, "__gh_username__", self.__gh_username__, "__gh_repo_name__", self.__gh_repo_name__,)
        if self.__gh_bearer_token__ == None or self.__gh_username__ == None or self.__gh_repo_name__ == None:
            raise Exception(f"To handle local file uploads to threads please provide your GitHub fine-grained access token, your GitHub username and the name of your GitHub repository to be used for the temporary file upload")
        
        if not filetype.is_image(file) and not filetype.is_video(file):
            self.__delete_uploaded_files__(files=self.__handled_media__)
            raise Exception(f"Provided file at index {file_index} must be either an image or video file, {filetype.guess_mime(file)} given")
        
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
            raise Exception(f"An unknown error occured while trying to upload local file at index {file_index} to GitHub, error:", e)

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

# t = ThreadsPipe()

