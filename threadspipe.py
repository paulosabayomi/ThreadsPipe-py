import requests, io, base64, time, logging, re, math, filetype, apivideo, os, string, random
import urllib.parse as urlp
from  typing import Optional, List, Any

from apivideo.apis import VideosApi
from apivideo.api import videos_api
from apivideo.model.too_many_requests import TooManyRequests
from apivideo.model.video_creation_payload import VideoCreationPayload
from apivideo.model.bad_request import BadRequest
from apivideo.model.video import Video


import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow


from dotenv import set_key

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

class ThreadsPipe:
    __threads_media_post_url__ = ""
    __threads_post_publish__ = ""

    __threads_post_limit__ = 500
    __threads_media_limit__ = 10
    __threads_rate_limit__ = 250

    __threads_access_token__ = ''
    __threads_user_id__ = ''

    __wait_before_post_publish__ = True
    __post_publish_wait_time__ = 30

    __handle_hashtags__ = True
    __auto_handle_hashtags__ = False

    __imgur_upload_api__ = "https://api.imgur.com/3/image"

    __imgur_client_id__ = "c1382ecc1854bbe"
    __imgur_client_secret__ = "49d7b0fcadf21478c022301ee928edcf6c849dce"
    
    __vimeo_client_id__ = "458e47ee193515fc180d51fa4e03e6ad38b411cd"
    __vimeo_access_token__ = "77231c0c09053a034af74455d79fefac"
    __vimeo_client_secret__ = "BOuVyGYW/DkvCLmaNYkaJkOtraPzsihYp50G/XVWaVA1oEIxnKGqATn1/pMORZqpXW/wjDnvDsmiEqRWULEIv1VLs9IWQnCJgohKVnqnKpkzGDKzK/D7RDKQY+VlJrmb"
    
    __api_dot_video_api_key__ = "cZEf0zQnatj7JlgWdEVNDoVjczqtOFg3GUqzJLAenhR"

    def __init__(
            self, 
            user_id: int, 
            access_token: str, 
            disable_logging = False,
            wait_before_post_publish = True,
            post_publish_wait_time = 30, # 30 seconds wait time before publishing a post
            handle_hashtags = True,
            auto_handle_hashtags = False
        ) -> None:

        self.__threads_access_token__ = access_token
        self.__threads_user_id__ = user_id

        self.__wait_before_post_publish__ = wait_before_post_publish
        self.__post_publish_wait_time__ = post_publish_wait_time

        self.__threads_media_post_url__ = f"https://graph.threads.net/v1.0/{user_id}/threads?access_token={access_token}"
        self.__threads_post_publish__ = f"https://graph.threads.net/v1.0/{user_id}/threads_publish?access_token={access_token}"

        self.__handle_hashtags__ = handle_hashtags

        self.__auto_handle_hashtags__ = auto_handle_hashtags

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

        print("files:", files)

        prev_post_chain_id = reply_to_id
        # for s_post in splitted_post:
        #     prev_post_chain_id = self.__send_post__(
        #         s_post, 
        #         medias=[],
        #         reply_to_id=prev_post_chain_id
        #     )

        


    def __send_post__(self, post: Optional[str], medias: Optional[List], reply_to_id: Optional[str] = None):
        is_carousel = len(medias) > 1
        media_cont = medias

        # for url in medias:
        #     get_url = requests.get(url)
        #     get_url.raise_for_status()
        #     media_type = get_url.headers['Content-Type'].split('/')[0].upper()
        #     media_cont.append({'type': media_type, 'url': url})

        MEDIA_CONTAINER_ID = ''
        post_text = f"&text={self.__quote_str__(post)}" if post is not None else ""

        if is_carousel:
            MEDIA_CONTAINER_IDS_ARR = []
            for media in media_cont:
                media_query = "image_url=" + media['url'] if media['type'] == 'IMAGE' else "video_url=" + media['url']
                carousel_post_url = f"{self.__threads_media_post_url__}&media_type={media['type']}&is_carousel_item=true&{media_query}"
                req_post = requests.post(carousel_post_url)
                req_post.raise_for_status()
                MEDIA_CONTAINER_IDS_ARR.append(req_post.json()['id'])
            
            media_ids_str = ",".join(MEDIA_CONTAINER_IDS_ARR)
            carousel_cont_url = f"{self.__threads_media_post_url__}&media_type=CAROUSEL&children={media_ids_str}{post_text}"
            req_create_carousel = requests.post(carousel_cont_url)
            req_create_carousel.raise_for_status()
            MEDIA_CONTAINER_ID = req_create_carousel.json()['id']
            
        else:
            media_type = "TEXT" if len(medias) == 0 else media_cont[0]['type']
            media = "" if len(medias) == 0 else media_cont[0]['url']
            media_url = "&image_url=" + media if media_type == "IMAGE" else "&video_url=" + media
            media_url = "" if len(medias) == 0 else media_url
            make_post_url = f"{self.__threads_media_post_url__}&media_type={media_type}{media_url}{post_text}"
            request_endpoint = requests.post(make_post_url)
            request_endpoint.raise_for_status()
            MEDIA_CONTAINER_ID = request_endpoint.json()['id']

        try:
            if self.__wait_before_post_publish__:
                time.sleep(self.__post_publish_wait_time__)
            reply_to_id = "" if reply_to_id is None else f"&reply_to_id={reply_to_id}"
            publish_post_url = f"{self.__threads_post_publish__}&creation_id={MEDIA_CONTAINER_ID}{reply_to_id}"
            publish_post = requests.post(publish_post_url)
            publish_post.raise_for_status()
            post_debug = self.__debug_post__(MEDIA_CONTAINER_ID)
            if post_debug['status'] != 'FINISHED':
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
    
    def __debug_post__(self, media_id: int):
        media_debug_endpoint = f"https://graph.threads.net/v1.0/{media_id}?fields=status,error_message&access_token={self.__threads_access_token__}"
        req_debug_response = requests.get(media_debug_endpoint)
        req_debug_response.raise_for_status()
        return req_debug_response.json()
    
    def __split_post__(self, post: str, tags: List) -> List[str]:
        if len(post) <= self.__threads_post_limit__:
            first_tag = "" if len(tags) == 0 else "\n"+tags[0].strip()
            first_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post) else first_tag
            return [post + first_tag]
        
        tagged_post = []
        untagged_post = []

        clip_tags = tags[:math.ceil(len(post) / self.__threads_post_limit__)]

        prev_strip = 0
        for i in range(len(clip_tags)):
            _tag = "\n"+clip_tags[i].strip()
            extra_strip = 3 if i == 0 else 6
            prev_tag = len("\n"+clip_tags[i - 1].strip()) + extra_strip if i > 0 else len("\n"+clip_tags[i].strip()) + extra_strip
            pre_dots = "" if i == 0 else "..."
            sub_dots = "..." if i + 1 < len(clip_tags) else ""
            put_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post[(self.__threads_post_limit__ * i) : (self.__threads_post_limit__ * (i+1))]) else _tag
            start_strip = prev_tag
            _post = pre_dots + post[(self.__threads_post_limit__ * i) - prev_strip : (self.__threads_post_limit__ * (i + 1)) - (extra_strip + prev_strip + len(put_tag))] + sub_dots + put_tag
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
                _post = pre_dots + post[(self.__threads_post_limit__ * i) - start_strip : (self.__threads_post_limit__ * (i + 1)) - (extra_strip + start_strip)] + sub_dots
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
        handled_media = []

        for file in media_files:
            url_file = re.compile(r"^(https?:\/\/)?([a-zA-Z0-9]+\.)?[a-zA-Z0-9]+\.[a-zA-Z0-9]{2,}(\/.*)?$")
            if type(file) == str and url_file.match(file):
                media_type = filetype.get_type(ext=file.split('.')[-1])
                if media_type == None:
                    raise Exception(f"Filetype of the file at index {media_files.index(file)} is invalid")
                media_type = media_type.mime.split('/')[0].upper()
                handled_media.append({ 'type': media_type, 'file': file })
                continue
            elif self.__is_base64__(file):
                handled_media.append(self.__get_file_url__(base64.b64decode(file), media_files.index(file)))
            else:
                handled_media.append(self.__get_file_url__(file, media_files.index(file)))

        return handled_media
    
    def __get_file_url__(self, file, file_index: int):
        if not filetype.is_image(file) and not filetype.is_video(file):
            raise Exception(f"Provided file at index {file_index} must be either an image or video file, {filetype.guess_mime(file)} given")
        f_type = "IMAGE" if filetype.is_image(file) else "VIDEO"

        file_obj = {
            'type': f_type,
        }

        if f_type == "IMAGE":
            if self.__imgur_client_id__ == None:
                raise Exception("Imgur Client ID is required")
            # file = open(file, 'rb').read() if type(file) == str else file
            # req_to_imgur = requests.post(
            #     self.__imgur_upload_api__,
            #     files={ 'image': file },
            #     headers={ 'Authorization': 'Client-ID ' + self.__imgur_client_id__ }
            # )
            # req_to_imgur.raise_for_status()
            # upload_resp = req_to_imgur.json()
            # if not upload_resp['success'] == True:
            #     raise Exception(f'Image file at index {file_index} attempt to upload to imgur failed')
            # file_obj['url'] = upload_resp['data']['link']
            # file_obj['id'] = upload_resp['data']['deletehash']
        else:
            # vimeo_api = vimeo.VimeoClient(token=self.__vimeo_access_token__, key=self.__vimeo_client_id__, secret=self.__vimeo_client_secret__)
            _f_type = filetype.guess(file).mime
            file = open(file, 'rb').read() if type(file) == str else file
            file_path = os.path.join(os.path.abspath('.'), self.__rand_str__(10)+'.'+_f_type.split('/')[-1])
            with open(file_path, 'wb') as f:
                f.write(file)
            # try:
            #     uploaded_vid = vimeo_api.upload(file_path)
            #     os.unlink(file_path)
            #     time.sleep(5)
            #     vid = vimeo_api.get(uploaded_vid)
            #     print("uploaded_vid", uploaded_vid, vid.json(), '\n\n\n', vid.json(), 'download' in vid.json(), 'files' in vid.json())
            # except Exception as e:
            #     # os.unlink(file_path)
            #     logging.error(e)
                
            # try:
            #     api_client = apivideo.AuthenticatedApiClient(self.__api_dot_video_api_key__)
            #     api_client.connect()

            #     api_instance = videos_api.VideosApi(api_client)
            #     video_creation_payload = VideoCreationPayload(
            #         title="Video for threads",
            #         # source=open(file_path, 'rb').read(),   
            #         # source="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",   
            #     )
            #     api_response = api_instance.create(video_creation_payload)
            #     print("api_response", api_response)

            #     # api_instance = videos_api.VideosApi(api_client)
            #     video_id = api_response['video_id'] # str | Enter the videoId you want to use to upload your video.
            #     file = open(file_path, 'rb')
            #     api_response = api_instance.upload(video_id, file)
            #     print("\n\n\n\n\napi_response 222", api_response)
            #     os.unlink(file_path)

            # except Exception as e:
            #     if os.path.exists(file_path):
            #         os.unlink(file_path)
            #     print(e)
                
            CLIENT_SECRETS_FILE = './client_secret.json'
            SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
            API_SERVICE_NAME = 'youtube'
            API_VERSION = 'v3'

            VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')

            def get_authenticated_service():
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                # credentials = flow.run_console()
                credentials = flow.run_local_server(port=0)
                return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)
                
            def initialize_upload(youtube, options):
                tags = None
                # if options.keywords:
                #     tags = options.keywords.split(',')

                body=dict(
                    snippet=dict(
                        title="threads video",
                    ),
                    status=dict(
                        privacyStatus="unlisted"
                    )
                )

                # Call the API's videos.insert method to create and upload the video.
                insert_request = youtube.videos().insert(
                    part=','.join(body.keys()),
                    body=body,
                    # The chunksize parameter specifies the size of each chunk of data, in
                    # bytes, that will be uploaded at a time. Set a higher value for
                    # reliable connections as fewer chunks lead to faster uploads. Set a lower
                    # value for better recovery on less reliable connections.
                    #
                    # Setting 'chunksize' equal to -1 in the code below means that the entire
                    # file will be uploaded in a single HTTP request. (If the upload fails,
                    # it will still be retried where it left off.) This is usually a best
                    # practice, but if you're using Python older than 2.6 or if you're
                    # running on App Engine, you should set the chunksize to something like
                    # 1024 * 1024 (1 megabyte).
                    media_body=MediaFileUpload(options.file, chunksize=-1, resumable=True)
                )

                print("insert_request", insert_request)

            youtube = get_authenticated_service()
            initialize_upload(youtube, {
                file: open(file_path, 'rb').read()
            })
            # try:
            
            #     req_vid_obj = requests.post(
            #         "https://ws.api.video/videos",
            #         headers={
            #             "Content-Type": "application/json",
            #             "Authorization": "Basic " + self.__api_dot_video_api_key__
            #         },
            #         data={
            #             "title": "Video for threads"
            #         },
            #         # verify=False
            #     )

            #     req_vid_obj.raise_for_status()

            #     vid_obj = req_vid_obj.json()

            #     # file_byte = open(file_path, 'rb').read()

            #     req_upl_vid = requests.post(
            #         f"https://ws.api.video/videos/{vid_obj['id']}/source",
            #         headers={
            #             "Authorization": "Basic " + self.__api_dot_video_api_key__
            #         },
            #         data={
            #             "title": "Video for threads"
            #         },
            #         files={
            #             'file': open(file_path, 'rb').read()
            #         },
            #         # verify=False
            #     )

            #     req_upl_vid.raise_for_status()

            #     upl_vid_resp = req_upl_vid.json()

            #     print("upl_vid_resp:", upl_vid_resp)
            # except Exception as e:
            #     os.unlink(file_path)
            #     print(e)

        return file_obj
    

# t = ThreadsPipe()

