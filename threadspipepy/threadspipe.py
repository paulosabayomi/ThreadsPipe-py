"""
    threadspipe uses the official Meta's Threads API to perform actions on a user's account,
    actions like create post, respond to posts and replies, get posts and users account insights and many more.
"""

import requests, base64, time, logging, re, math, filetype, string, random, datetime, webbrowser, os
import urllib.parse as urlp

from  typing import Optional, List, Any, Union
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

    __threads_api_version__ = 'v1.0'

    __threads_post_length_limit__ = 500
    __threads_media_limit__ = 10

    __threads_rate_limit__ = 250
    __threads_reply_rate_limit__ = 1000

    __threads_access_token__ = ''
    __threads_user_id__ = ''

    __wait_before_post_publish__ = True
    __post_publish_wait_time__ = 35

    __wait_before_media_item_publish__ = True
    __media_item_publish_wait_time__ = 35

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

    __file_url_reg__ = re.compile(r"(?P<url>((https?:\/\/)?[^\s\/]+?\.?)?(([a-zA-Z0-9]+\.[\w]{2,})|([\d]{1,}\.[\d]{1,}\.[\d]{1,}\.[\d]{1,}))([\:\d]+)?\/?([a-zA-Z0-9\.\-\_\/]+)?(\?[a-zA-Z0-9\.\&\#\=\-\_\%\?]+)?)$")

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
            disable_logging: bool = False,
            wait_before_post_publish: bool = True,
            post_publish_wait_time: int = 35, # 35 seconds wait time before publishing a post
            wait_before_media_item_publish: bool = True,
            media_item_publish_wait_time: int = 35, # 35 seconds wait time before publishing a post
            handle_hashtags: bool = True,
            auto_handle_hashtags: bool = False,
            gh_bearer_token: str = None,
            gh_api_version: str = "2022-11-28",
            gh_repo_name: str = None,
            gh_username: str = None,
            gh_upload_timeout: int = 60 * 5,
            wait_on_rate_limit: bool = False,
            check_rate_limit_before_post: bool = True,
            threads_api_version: str = 'v1.0'
        ) -> None:

        """
            # ThreadsPipe
            ## Parameters
            ### Example   
            ```py
                import threadspipe
                #...

                api = threadspipe.ThreadsPipe(
                    access_token="threads-access-token", 
                    user_id="threads-user-id", 
                    handle_hashtags=True, 
                    auto_handle_hashtags=False, 
                    gh_bearer_token = "your-github-fined-grained-token",
                    gh_repo_name = 'the-repository-name',
                    gh_username = 'your-github-username',
                )
            ```

            user_id: `int`  \
            The user_id of the Threads account, which is part of the data returned when you call the `get_access_tokens` method

            access_token: `str` The user's account access token, \
            either the short or long lived access token can be used, but the long lived access token is recommended, \
            the short and long lived access token are part of the data returned when you call the `get_access_tokens` method

            disable_logging - `bool | False` \
            By default ThreadsPipe displays logs using the python's `logging` module, if you want to disable logging set this to `False`

            wait_before_post_publish: `bool | True` \
            It is recommended to wait for the status of media items (or uploaded files) or media containers (post blueprints) \
            to be 'FINISHED' before publishing a Threads media container, the average wait time is 30 seconds \
            and trying to publish a media item/file, and media container / post before it has finished processing could cause the publishing of the media container/post to fail, \
            it is recommended to leave this parameter to `True`.

            post_publish_wait_time: `int | 35` \
            The time to wait for a media container or post in seconds to finish processing before publishing it, \
            **Note:** it must not be less than 30 seconds and it is recommended not to be less than 31 seconds.

            wait_before_media_item_publish: `bool | True` \
            Media item (AKA uploaded files), just like media containers/posts, it is also recommended to wait for media items or uploaded files \
            to finish processing before publishing the media container or post it is attached to.

            media_item_publish_wait_time: `int | 35` \
            The time to wait for a media item/uploaded files to finish processing, different media item types \
            have different processing time and image files with small file sizes are always processed quickly than ones with larger \
            file sizes and video files.

            handle_hashtags: `bool | True` \
            ThreadsPipe automatically handle hastags that are added to the end of a post, because only \
            one hashtag is allowed in a threads post, so the tags are extracted and splitted and added to each of the chained posts, \
            To not automatically handle hashtags set this to `False` \
            if the text in the post is longer than the maximum character allowed by threads for a post or the provided files \
            are more than the maximum allowed the post will be splitted and chained to the root post \
            which is going to be like a thread post on X. The body of the post might already have an hashtag \
            to make it more dynamic set the `auto_handle_hashtags` to `True`, when `auto_handle_hashtags` is `True` \
            the post body that already has an hashtag will be skipped and no hashtag will be added to it.

            auto_handle_hashtags: `bool | False` \
            When this is `True` it will more intelligently (that what the `handle_hashtags` option does) and automatically handle hashtags, \
            in cases where there are many hashtags at the end of a posts, the hashtags will be extracted and distributed intelligently \
            between the chained posts, posts that already have an hashtag within the body of the post will not be given an hashtag.

            gh_bearer_token: `str | None` \
            Your GitHub fine-grained token, which can be gotten from [https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta), \
            Because to upload files to the Threads API, only the url to the files are allowed and the files must be on a public server, \
            and this is going to be challenging when uploading files available locally on your computer \
            or local files on a server that are not exposed to the public, that's why ThreadsPipe will first of all upload the \
            local files in the provided files to GitHub and then delete them after the files are uploaded to Threads or \
            if an error occured while trying to publish the post.
            
            gh_api_version: `str | '2022-11-28'` \
            The GitHub API version

            gh_repo_name: `str | None` \
            The name of the repository that should be used for the temporary storage of the local files.

            gh_username: `str | None` \
            Your GitHub username

            gh_upload_timeout: `int` \
            The upload timeout of the local files to GitHub, the default is `60 * 5` (5 minutes), \
            but you can either reduce it or increase it.

            wait_on_rate_limit: `bool | False` \
            Whether ThreadsPipe should wait when rate limit is hit instead of rejecting the request, this can have an impact on the memory on your server \
            in scenarios where multiple requests are made and will spawn multiple waiting processes.
            
            check_rate_limit_before_post: `bool | True` \
            By default ThreadsPipe checks rate limit everytime before proceeding to post, \
            if you don't want it to perform the check you can set it to `False`

            threads_api_version: `str | 'v1.0'` \
            Set this parameter to the Meta's Threads API version you want to use, default is `v1.0`
        """

        self.__threads_access_token__ = access_token
        self.__threads_user_id__ = user_id

        self.__threads_api_version__ = threads_api_version

        self.__wait_before_post_publish__ = wait_before_post_publish
        self.__post_publish_wait_time__ = post_publish_wait_time

        self.__wait_before_media_item_publish__ = wait_before_media_item_publish
        self.__media_item_publish_wait_time__ = media_item_publish_wait_time

        self.__threads_media_post_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads?access_token={access_token}"
        self.__threads_post_publish_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads_publish?access_token={access_token}"
        self.__threads_rate_limit_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads_publishing_limit?access_token={access_token}"
        self.__threads_post_reply_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/me/threads?access_token={access_token}"
        self.__threads_profile_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/me?access_token={access_token}"

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


    def update_param(
            self, 
            user_id: int = None, 
            access_token: str = None, 
            disable_logging: bool = None,
            wait_before_post_publish: bool = None,
            post_publish_wait_time: int = None, # 35 seconds wait time before publishing a post
            wait_before_media_item_publish: bool = None,
            media_item_publish_wait_time: int = None, # 35 seconds wait time before publishing a post
            handle_hashtags: bool = None,
            auto_handle_hashtags: bool = None,
            gh_bearer_token: str = None,
            gh_api_version: str = None,
            gh_repo_name: str = None,
            gh_username: str = None,
            gh_upload_timeout: int = None,
            wait_on_rate_limit: bool = None,
            check_rate_limit_before_post: bool = None,
            threads_api_version: str = None
        ) -> None:

        """
            ## ThreadsPipe.update_param

            ### Description
            To update the default class parameters, it is not guaranteed that the updated \
            value(s) of the parameter(s) will be used if this method is called before performing an \
            action with the parameter(s) that was set with the method, so it is recommended to call this \
            method to set the parameter(s) before performing the action(s) with the parameter(s) that was set.

            #### Example   
            ```py
                api.update_param(
                    user_id=user_id,
                    access_token=access_token,
                    disable_logging=True
                )
            ```

            ### Parameters
            See the class object __init__ for more info on the parameters 
        """

        if access_token is not None:
            self.__threads_access_token__ = access_token
            self.__threads_post_reply_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/me/threads?access_token={access_token}"
            self.__threads_profile_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/me?access_token={access_token}"
            
        if user_id is not None:
            self.__threads_user_id__ = user_id

        if wait_before_post_publish is not None:
            self.__wait_before_post_publish__ = wait_before_post_publish
        if post_publish_wait_time is not None:
            self.__post_publish_wait_time__ = post_publish_wait_time

        if wait_before_media_item_publish is not None:
            self.__wait_before_media_item_publish__ = wait_before_media_item_publish
        if media_item_publish_wait_time is not None:
            self.__media_item_publish_wait_time__ = media_item_publish_wait_time

        if user_id is not None and access_token is not None:
            self.__threads_media_post_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads?access_token={access_token}"
            self.__threads_post_publish_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads_publish?access_token={access_token}"
            self.__threads_rate_limit_endpoint__ = f"https://graph.threads.net/{self.__threads_api_version__}/{user_id}/threads_publishing_limit?access_token={access_token}"
        
        if handle_hashtags is not None:
            self.__handle_hashtags__ = handle_hashtags

        if threads_api_version is not None:
            self.__threads_api_version__ = threads_api_version

        if auto_handle_hashtags is not None:
            self.__auto_handle_hashtags__ = auto_handle_hashtags

        if gh_bearer_token is not None:
            self.__gh_bearer_token__ = gh_bearer_token
        if gh_api_version is not None:
            self.__gh_api_version__ = gh_api_version
        if gh_username is not None:
            self.__gh_username__ = gh_username
        if gh_repo_name is not None:
            self.__gh_repo_name__ = gh_repo_name
        if gh_upload_timeout is not None:
            self.__gh_upload_timeout__ = gh_upload_timeout

        if wait_on_rate_limit is not None:
            self.__wait_on_rate_limit__ = wait_on_rate_limit
        if check_rate_limit_before_post is not None:
            self.__check_rate_limit_before_post__ = check_rate_limit_before_post

        if disable_logging is not None and disable_logging is True:
            logging.disable()

    def pipe(
            self, 
            post: Optional[str] = "", 
            files: Optional[List] = [], 
            file_captions: List[Union[str, None]] = [],
            tags: Optional[List] = [],
            reply_to_id: Optional[str] = None, 
            who_can_reply: Union[str, None] = None,
            chained_post = True, 
            persist_tags_multipost = False,
            allowed_country_codes: Union[str, List[str]] = None,
            link_attachments: List[str] = [],
        ):

        """
            ## ThreadsPipe.pipe

            ### Description   
            The pipe method is for sending posts and replies to Threads

            ### Example

            ```py
                pipe = api.pipe(
                            post="A very long text...",
                            files=[
                                "/path/to/img-2.jpg",
                                "https://example.com/video-1482062364825.mp4",
                                open('/path/to/img-1.jpg', 'rb').read(),
                                "https://example.com/photo-1504639725590.jpg",
                                open('sample-5.mp4', 'rb').read(),
                                "https://example.com/photo-1721332149371.jpg"
                                "https://example.com/?w=800&p=Mnx8fGVufD%3D%3D",
                                "https://example.com/photo-1725647093138.png",
                                "https://example.com/?q=80&w=2574&z=jhsdbcjh",
                                "https://example.com/?q=80&w=2574&z=awdas",
                                "https://example.com/photo-1725628736546.mp4",
                                "https://example.com/?w=800&p=nx8fGVA%3D%3D",
                                "https://example.com/photo-1725792630033.jpeg",
                                "https://example.com/?q=80&w=2574&z=wqfwefe",
                                "https://example.com/photo-1725462567088.png"
                                #...
                            ],
                            allowed_country_codes=["US", "CA", "NG", "SG"]
                            file_captions=[
                                'image of a macbook on a white table', 
                                "image 1 from example website", 
                                "coding picture taken upclose", None, 
                                "video of watering a garden flower", 
                                None, None, None, None, 
                                "Image second from example website", None, None, 
                                "Another third image from example website", None, 
                                "Image 4 from example website", 
                                None, 
                                "Image 5 from example website", None],
                            who_can_reply="accounts_you_follow"
                        )
            ```

            ### Parameters

            post: `str | ""` \
            This parameter takes a string which is the text content of the post, \
            it can be of any length and can be more than 500 which is the current \
            character limit allowed in a post, ThreadsPipe will split the text \
            into different batches of 500 characters, if the provided text is more than 500 \
            and upload the first batch as the root post and \
            then upload the rest of the batches as a reply to the root post, then the resulting post is going \
            to be like an X thread post.

            files: `List | []` \
            The media files that will be attached to the post, the allowed file types \
            can be `bytes`, url to a file, and `base64`, you can also pass in the path to a local file, \
            the number of files can be any length and more than 10, if the number of files \
            is more than 10 which is the limit for a post, ThreadsPipe would split them into batches of 10 files \
            and send the first batch with the first text batch and the rest of the batch either as replies to the \
            root post (if the text content of the post is less than 500) or with the text batch reply(ies) to the \
            root post.

            file_captions: `List[str | None] | []` \
            The captions for the media files, provide the captions based on the index of the provided files and provide `None` \
            at the index of the files that does not have caption, the length of the provided caption does not have to match the number of files provided, \
            for example if 5 files were provided, to provided captions for files at index 1 and 4 \
            it would be `[None, "Caption for file at index 1", None, None, "Caption for file at index 4"]`.

            tags: `List[str] | []` \
            If you would like to provide the hashtags instead of adding them to the end of the text content, \
            you can provide them with this property instead, they can be any length, this will have no effect if \
            both `handle_hashtags` and `auto_handle_hashtags` are `False`, Learn more about the `handle_hashtags` and `auto_handle_hashtags` \
            to understand them better.

            reply_to_id: `str | None` \
            To reply to a post pass in the media id of the target post that you want to reply to, \
            replying to a post also behaves like normal post and the text content and files will also be handled \
            the same way.

            who_can_reply: `str | None` \
            Use this parameter to set who can reply to the post you're sending, use the \
            `ThreadsPipe.who_can_reply_list` property to get a list of all available options, \
            supported options are and one of `'everyone'`, `'accounts_you_follow'`, and `'mentioned_only'`
            
            chained_post: `bool | True` \
            To turn off the automatic post chaining when the provided text content and/or the files are \
            above the limit set this parameter to `False`.

            persist_tags_multipost: `bool | False` \
            Set this parameter to `True` if you want either the hashtags at the end of the provided text content \
            or the provided hashtags to not be splitted and just be added as they are, this is useful only if you \
            are using a single hashtag and you want the hashtag to be added to each of the chained posts.

            allowed_country_codes: `List[str] | []` \
            This requires the user to have the geo-gating permission, if you want to restrict the post to a country or a set of countries, provide the list of \
            allowed country codes to this parameter, the format should be either a comma separated country codes \
            i.e. "US,CA,NG" or a `List` of the allowed country codes i.e. ["US","CA","NG"], \
            you can check if you have the permission to use the geo-gating feature by calling the `ThreadsPipe.is_eligible_for_geo_gating`

            link_attachments: `List[str] | None` \
            Use this to explicitly provide link(s) for the post, this will only work for text-only posts, if the number of links are more than 1 and \
            the post was splitted into a chained post, see the `pipe` method's `post` parameter doc for more info on chained posts, \
            then in this case because only one link is allowed per post the links will be shared among the \
            chained posts.  

            ### Returns
            dict | requests.Response | Response
        """

        if len(files) == 0 and (post is None or post == ""):
                raise Exception("Either text or at least 1 media (image or video) or both must be provided")
        
        tags = tags

        _post = post.strip()

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
            extract_tags = [] if len(extract_tags_reg.findall(_post)) == 0 else extract_tags_reg.findall(_post)[0].split(' ')
            tags = tags if len(tags) > 0 else extract_tags
            tags = [" ".join(tags) for _ in range(len(tags))] if persist_tags_multipost is True else tags
            _post = _post if len(extract_tags) == 0 else extract_tags_reg.sub('', _post).strip()

        splitted_post = self.__split_post__(_post, tags)
        splitted_post = [splitted_post[0]] if chained_post == False else splitted_post

        _captions = [file_captions[x] if x < len(file_captions) else None for x in range(len(files))]

        files = files[:self.__threads_media_limit__] if chained_post is False else files
        files = self.__handle_media__(files)
        if 'error' in files:
            return files
        splitted_files = [files[self.__threads_media_limit__ * x: self.__threads_media_limit__ * (x + 1)] for x in range(math.ceil(len(files)/self.__threads_media_limit__))]

        splitted_captions = [_captions[self.__threads_media_limit__ * x: self.__threads_media_limit__ * (x + 1)] for x in range(math.ceil(len(files)/self.__threads_media_limit__))]

        allowed_country_codes = allowed_country_codes if type(allowed_country_codes) is str else None if allowed_country_codes is None else ",".join(allowed_country_codes)

        media_ids = []
        prev_post_chain_id = None if reply_to_id is None else {'id': reply_to_id}
        for s_post in splitted_post:
            prev_post_chain_id = self.__send_post__(
                s_post, 
                medias=[] if splitted_post.index(s_post) >= len(splitted_files) else splitted_files[splitted_post.index(s_post)],
                media_captions=[] if splitted_post.index(s_post) >= len(splitted_captions) else splitted_captions[splitted_post.index(s_post)],
                reply_to_id=None if prev_post_chain_id is None else prev_post_chain_id['id'],
                allowed_listed_country_codes=allowed_country_codes,
                who_can_reply=who_can_reply,
                attached_link=link_attachments[splitted_post.index(s_post)] if splitted_post.index(s_post) < len(link_attachments) else None
            )
            if 'error' in prev_post_chain_id:
                return prev_post_chain_id
            else:
                media_ids.append(prev_post_chain_id['id'])
        
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

        self.__delete_uploaded_files__(files=files)
        logging.info("Post piped to Instagram Threads successfully!")
        return self.__tp_response_msg__(
            message='Post piped to Instagram Threads successfully!',
            is_error=False,
            response=prev_post_chain_id['publish_post'],
            body={'media_ids': media_ids}
        )

        
    def get_quota_usage(self, for_reply=False):
        """
            ## ThreadsPipe.get_quota_usage

            ### Description   
            The method to get user's quota usage

            ### Parameters

            for_reply: `bool | False` \
            Set this parameter to `True` to get the media reply / post reply quota usage, \
            default is `False` which returns the quota usage for posts.

            ### Returns
            requests.Response | Response | None
        """
        
        field = "&fields=reply_quota_usage,reply_config" if for_reply == True else "&fields=quota_usage,config"
        req_rate_limit = requests.get(self.__threads_rate_limit_endpoint__ + field)
            
        if 'data' in req_rate_limit.json():
            return req_rate_limit.json()
        else:
            return None
        
    def get_auth_token(self, app_id: str, redirect_uri: str, scope: Union[str, List[str]] = 'all', state: Union[str, None] = None):
        """
            ## ThreadsPipe.get_auth_token

            ### Description
            Use this method to implement the Authorization Window, The Authorization Window \
            allows your app to get authorization codes and permissions from app users. \
            Authorization codes can be exchanged for Threads user access tokens, which must be included when \
            fetching an app user's profile, retrieving Threads media, publishing posts, reading replies, managing \
            replies, or viewing insights.

            ### Parameters
            app_id: `str` \
            Your Threads app id which can be found on the `Use cases > Customize > Settings` page.

            redirect_uri: `str` \
            The uri that the Threads API will redirect the user to after granting or rejecting the permission \
            request, you can provide one of the redirect uri that you listed in the Redirect Callback URLs input box, \
            the user will be redirected to this url after the action with a `code` query parameter containing \
            authentication token which can be used to get short and long lived access tokens. \
            The resulting url after redirection will look like `https://example.com/api.php?code=dnsdbcbdkvv...#_` \
            and notice the `#_` at the end of the token which is not part of the token and should be \
            stripped off, **Note:** The authentication token can only be used once, see `get_access_tokens` method to learn more.

            scope: `str | List[str]` \
            The scope is the Threads permissions that are enabled for the app, you can leave the value of this parameter as `all` \
            or provide the list of comma separated string or `List` of the enabled permissions, the values should be \
            from one of ThreadsPipe library threads-auth-scopes, which you can get by calling `ThreadsPipe.__threads_auth_scope__`, \
            the returned dict's keys will be `basic`, `publish`, `read_replies`, `manage_replies`, `insights`.

            state: `str` \
            The state is a code to be set to prevent CORF e.g. '1', this is *optional*

            ### Returns
            None
        """
        
        scope = [x for x in self.__threads_auth_scope__.values()] if type(scope) == str and scope == 'all' else [self.__threads_auth_scope__[x] for x in scope]
        scope = ','.join(scope)
        state = f"&state={state}" if state is not None else ""
        url = f'https://threads.net/oauth/authorize/?client_id={app_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}{state}'
        webbrowser.open(url)

    def get_access_tokens(self, app_id: str, app_secret: str, auth_code: str, redirect_uri: str):
        """
            ## ThreadsPipe.get_access_tokens

            ### Description
            This method swaps the access token gotten from Authorization Window for short and long lived access token.

            ### Parameters

            app_id: `str` \
            The same app id you used when getting the authentication code from the Authentication Window.

            app_secret: `str` \
            This can be gotten from the `Use cases > Customize > Settings` page in the Threads App secret input box, \
            in the app dashboard.

            auth_code: `str` \
            The authentication code that was gotten from the redirect url of the Authorization Window, \
            Note this code can only be used once.

            redirect_uri: `str` \
            This redirect uri should be the same as the value of the `redirect_uri` argument passed to the `get_auth_token` \
            method or the request will be rejected and the authorization token will be expired.

            ### Returns
            dict | JSON
        """
        
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
        """
            ## ThreadsPipe.refresh_token

            ### Description
            Use this method to refresh unexpired long lived access tokens before they expire, long \
            lived access tokens expire after 60 days, and you can only refresh long lived token and \
            anytime after it is at least 24 hours old.

            ### Parameters
            access_token: `str` \
            The long lived access token that will be refreshed for a new and life-extended one.

            env_path: `str | None` \
            This is optional, and it is useful and only required if you want ThreadsPipe to automatically update a variable \
            with the new long lived token access token.

            env_variable: `str | None` \
            The name of the variable that ThreadsPipe should automatically update with the newly \
            generated long lived access token.

            ### Returns
            JSON
        """
        
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
        """
            ## ThreadsPipe.is_eligible_for_geo_gating

            ### Description
            Use this method to check for an account's eligibility for posting geo-gated contents

            ### Parameters
            None

            ### Returns
            JSON
        """
        
        url = self.__threads_profile_endpoint__ + "&fields=id,is_eligible_for_geo_gating"
        send_request = requests.get(url)
        if send_request.status_code != 200:
            logging.error(f"Could not get geo gating eligibility from Threads, Error:: {send_request.json()}")
            return self.__tp_response_msg__(
                message="Could not get geogating eligibility from Threads",
                body=send_request.json(),
                response=send_request,
                is_error=True
            )
        return send_request.json()
    
    def get_allowlisted_country_codes(self, limit: Union[str, int] = None):
        """
            ## ThreadsPipe.get_allowlisted_country_codes

            ### Description
            Use this method to get a list of the country code values that can be used to limit geo-gating contents

            ### Parameters
            limit: `str | int | None` \
            Use this parameter to limit the amount of data returned.

            ### Returns
            JSON
        """
        
        ret_limit = "" if limit == None else "&limit=" + str(limit)
        url = self.__threads_post_reply_endpoint__ + f"&fields=id,allowlisted_country_codes{ret_limit}"
        request_list = requests.get(url)
        return request_list.json()

    def get_posts(self, since_date: Union[str, None] = None, until_date: Union[str, None] = None, limit: Union[str, int, None] = None):
        """
            ## ThreadsPipe.get_posts

            ### Description
            This method returns all the posts an account has posted including the replies

            ### Parameters
            since_date: `str | None` \
            Set the start of the date that the posts should be returned from

            until_date: `str | None` \
            Set the end of the date of the posts that will be returned

            limit: `str | int | None` \
            The limit of the posts that should be returned

            ### Returns
            JSON
        """
        
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"
        _limit = "" if limit is None else f"&limit={str(limit)}"
        url = self.__threads_post_reply_endpoint__ + f"&fields=id,media_product_type,media_type,media_url,permalink,owner,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post,link_attachment_url{since}{until}{_limit}"
        req_posts = requests.get(url)
        return req_posts.json()
    
    def get_post(self, post_id: str):
        """
            ## ThreadsPipe.get_post

            ### Description
            This method returns the data of a single post

            ### Parameter
            post_id: `str` \
            The id of the post you want to get the data

            ### Returns
            JSON
        """
        
        url = f"https://graph.threads.net/{self.__threads_api_version__}/{post_id}?fields=id,media_product_type,media_type,media_url,permalink,owner,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post,link_attachment_url&access_token={self.__threads_access_token__}"
        req_post = requests.get(url)
        return req_post.json()
    
    def get_profile(self):
        """
            ## ThreadsPipe.get_profile

            ### Description
            The method to get user profile

            ### Parameters
            None

            ### Returns
            JSON
        """


        url = self.__threads_profile_endpoint__ + f"&fields=id,username,name,threads_profile_picture_url,threads_biography"
        req_profile = requests.get(url)
        return req_profile.json()

    def get_post_replies(self, post_id: str, top_levels=True, reverse=False):
        """
            ## ThreadsPipe.get_post_replies

            ### Description
            The method to get post replies

            ### Parameters
            post_id: `str` \
            The of the post you want to get its replies

            top_levels: `bool | True` \
            Set this parameter to `False` if you want to get the deep level or simply \
            replies of replies of replies, by default the method get the top level replies.

            reverse: `bool | False` \
            Set this parameter to `True` if you want the returned data to be in reverse order

            ### Returns
            JSON
        """
        
        _reverse = "false" if reverse is False else "true"
        reply_level_type = "replies" if top_levels is True else "conversation"
        url = f"https://graph.threads.net/{self.__threads_api_version__}/{post_id}/{reply_level_type}?fields=id,text,timestamp,media_product_type,media_type,media_url,shortcode,thumbnail_url,children,has_replies,root_post,replied_to,is_reply,hide_status&reverse={_reverse}&access_token={self.__threads_access_token__}"
        req_replies = requests.get(url)
        return req_replies.json()
    
    def get_user_replies(self, since_date: Union[str, None] = None, until_date: Union[str, None] = None, limit: Union[int, str] = None):
        """
            ## ThreadsPipe.get_user_replies

            ### Description
            The method to get all user's replies

            ### Parameter
            since_date: `str | None` \
            The start of the date to return the data from

            until_date: `str | None` \
            The end date of the replies that will be returned

            limit: `int | str` \
            The limit of the data that should be returned

            ### Returns
            JSON
        """
        
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"
        _limit = "" if limit is None else f"&limit={str(limit)}"
        url = f"https://graph.threads.net/{self.__threads_api_version__}/me/replies?fields=id,media_product_type,media_type,media_url,permalink,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post,has_replies,root_post,replied_to,is_reply,is_reply_owned_by_me,reply_audience&since={since}&until={until}&limit={_limit}&access_token={self.__threads_access_token__}"
        req_replies = requests.get(url)
        return req_replies.json()
    
    def hide_reply(self, reply_id: str, hide: bool):
        """
            ## ThreadsPipe.hide_reply

            ### Description
            The method to hide a reply under a user's post

            ### Parameters
            reply_id: `str` \
            The id of the reply that you want to hide
            
            hide: `bool` \
            Can be `True` or `False`, set it to `True` if you want to hide the reply \
            and `False` to unhide the reply

            ### Returns
            JSON
        """
        
        _hide = "true" if hide is True else "false"
        url = f"https://graph.threads.net/{self.__threads_api_version__}/{reply_id}/manage_reply"
        req_hide_reply = requests.post(
            url,
            data={
                "access_token":self.__threads_access_token__,
                "hide": _hide
            }
        )
        return req_hide_reply.json()
    
    def get_post_insights(self, post_id: str, metrics: Union[str, List[str]] = 'all'):
        """
            ## ThreadsPipe.get_post_insights

            ### Description
            The method to get post insights, like number of like, view and so on

            ### Parameters
            post_id: `str` \
            The id of the post you want to get insights for
            
            metrics: `str | List[str] | 'all'` \
            The metrics to include in the data, leave the value of this parameter as 'all' to get data for all \
            the available metrics or pass in a list of the metrics you want either as a comma separated string \
            or as a `List`, you can get the list of metrics you can pass from the `ThreadsPipe.threads_post_insight_metrics` parameter \
            which are `'views'`, `'likes'`, `'replies'`, `'reposts'`, `'quotes'`.

            ### Returns
            JSON
        """
        
        _metric = ",".join(self.threads_post_insight_metrics) if metrics == 'all' else metrics
        _metric = ','.join(_metric) if type(_metric) is list else _metric
        _metric = "&metric=" + _metric
        url = f"https://graph.threads.net/{self.__threads_api_version__}/{post_id}/insights?access_token={self.__threads_access_token__}{_metric}"
        req_insight = requests.get(url)
        return req_insight.json()
    
    def get_user_insights(self, user_id: Union[str, None] = None, since_date: Union[str, None] = None, until_date: Union[str, None] = None, follower_demographic_breakdown: str = 'country', metrics: Union[str, List[str]] = 'all'):
        """
            ## ThreadsPipe.get_user_insights

            ### Description
            The method to get user's account insights

            ### Parameters
            user_id: `str | None` \
            The optional user id if you want to get the account insights for another user that's different from the currently connected one to ThreadsPipe.
            
            since_date: `str | None` \
            The start date that the data should be returned from, **Note:** that User insights are not guaranteed to work before June 1, 2024, \
            and the user insights since_date and until_date parameters do not work for dates before April 13, 2024
            
            until_date: `str | None` \
            The end date of the insights data, **Note:** The user insights `since_date` and `until_date` parameters do not work for dates before April 13, 2024.
            
            follower_demographic_breakdown: `str | 'country'` \
            The metrics contains the `'follower_demographics'` value which requires one follower demographic breakdown \
            to be provided, you can get the list of all available values that you can pass to this parameter \
            from the `ThreadsPipe.threads_follower_demographic_breakdown_list` which will return \
            `'country'`, `'city'`, `'age'`, and `'gender'` and only one of them should be provided.
            
            metrics: `str | List[str] | 'all'` \
            The metrics that should be returned for the user account's insight, you can either leave the default value of \
            this parameter as 'all' which will return all available metrics or provide a comma separated string of \
            the metrics you want or as a `List`, you can get the available user insight metrics from the `ThreadsPipe.threads_user_insight_metrics` \
            which will return `"views"`, `"likes"`, `"replies"`, `"reposts"`, `"quotes"`, `"followers_count"`, and `"follower_demographics"`.

            ### Returns
            JSON
        """
        
        _metric = ",".join(self.threads_user_insight_metrics) if metrics == 'all' else metrics
        _metric = ','.join(_metric) if type(_metric) is list else _metric
        _metric = "&metric=" + _metric
        _demographic_break_down = "&breakdown=" + follower_demographic_breakdown
        since = "" if since_date is None else f"&since={since_date}"
        until = "" if until_date is None else f"&until={until_date}"

        _user_id = user_id if user_id is not None else "me"

        url = f"https://graph.threads.net/{self.__threads_api_version__}/{_user_id}/threads_insights?access_token={self.__threads_access_token__}{_metric}{since}{until}{_demographic_break_down}"
        req_insight = requests.get(url)
        return req_insight.json()
    
    def get_post_intent(self, text: str = None, link: str = None):
        """
            ## ThreadsPipe.get_post_intent

            ### Description
            The method to get Threads' post intent

            ### Parameters
            text: `str | None` \
            The text content of the post

            ### link: `str | None` \
            The link to your blog or website

            ### Returns
            str
        """
        
        _text = "" if text is None else self.__quote_str__(text)
        _url = "" if link is None else "&url=" + urlp.quote(link,safe="")
        return f"https://www.threads.net/intent/post?text={_text}{_url}"
    
    def get_follow_intent(self, username: Union[str, None] = None):
        """
            ## ThreadsPipe.get_follow_intent

            ### Description
            The method to get the follow intent link, this intents allow people to easily follow a Threads account directly from your website.

            ### Parameters
            username: `str | None` \
            The username you want to get the follow intent for, leave this as `None` to automatically use the connected account.

            ### Returns
            str
        """
        
        _username = username if username is not None else self.get_profile()['username']
        return f"https://www.threads.net/intent/follow?username={_username}"


    def __send_post__(
            self, 
            post: str = None, 
            medias: Optional[List] = [], 
            media_captions: List[Union[str, None]] = [],
            reply_to_id: Optional[str] = None,
            allowed_listed_country_codes: Union[str, None] = None,
            who_can_reply: Union[str, None] = None,
            attached_link: Union[str, None] = None
        ):
        """
            ### ThreadsPipe.__send_post__

            #### Description
            This method handles sending posts and replies to Threads
        """
        
        
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
                        body=quota | {'status_code': 429},
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
                        response=req_post,
                        is_error=True
                    )

                logging.info(f"Media/file at index {media_cont.index(media)} uploaded {req_post.json()}")

                media_debug = self.__get_uploaded_post_status__(req_post.json()['id'])
                f_info = f"\n::Note:: waiting for the upload status of the media item/file at index {media_cont.index(media)} to be 'FINISHED'" if media_debug.json()['status'] != "FINISHED" else ''
                logging.info(f"Media upload debug for media/file at index {media_cont.index(media)}:: {media_debug.json()}{f_info}")
                while media_debug.json()['status'] != "FINISHED":
                    time.sleep(self.__media_item_publish_wait_time__)
                    media_debug = self.__get_uploaded_post_status__(req_post.json()['id'])
                    f_info = f"\n::Note:: waiting for the upload status of the media item/file at index {media_cont.index(media)} to be 'FINISHED'" if media_debug.json()['status'] != "FINISHED" else ''
                    logging.info(f"Media upload debug for media/file at index {media_cont.index(media)}:: {media_debug.json()}{f_info}")
                    if media_debug.json()['status'] == 'ERROR':
                        self.__delete_uploaded_files__(files=self.__handled_media__)
                        logging.error(f"Media item / file at index {media_cont.index(media)} could not be published, Error:: {media_debug.json()}")
                        return self.__tp_response_msg__(
                            message=f"Media item / file at index {media_cont.index(media)} could not be published", 
                            body=media_debug.json(),
                            response=media_debug,
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
                    response=req_create_carousel,
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
            
            caption = None if len(media_captions) == 0 else media_captions[0]
            caption = None if caption is None else {"alt_text": caption}
            attached_link_query = "&link_attachment=" + urlp.quote(attached_link,safe="") if attached_link is not None and len(medias) == 0 else ""
            make_post_url = f"{endpoint}&media_type={media_type}{media_url}{post_text}{reply_to_id}{allowed_countries}{reply_control}{attached_link_query}"

            request_endpoint = requests.post(make_post_url, json=caption)
            
            if request_endpoint.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                logging.error(f"An error occured while creating media, Error:: {request_endpoint.json()}")
                return self.__tp_response_msg__(
                    message="An error occured while creating media / single post blueprint", 
                    body=request_endpoint.json(),
                    response=request_endpoint,
                    is_error=True
                )

            MEDIA_CONTAINER_ID = request_endpoint.json()['id']

        delete_gh_files = True
        try:
            post_debug = self.__get_uploaded_post_status__(MEDIA_CONTAINER_ID)
            d_info = '\n::Note:: waiting for the post\'s ready status to be \'FINISHED\'' if post_debug.json()['status'] != 'FINISHED' else ''
            logging.info(f"Post publish-ready status:: {post_debug.json()}{d_info}")

            while post_debug.json()['status'] != 'FINISHED':
                time.sleep(self.__post_publish_wait_time__)
                post_debug = self.__get_uploaded_post_status__(MEDIA_CONTAINER_ID)
                d_info = '\n::Note:: waiting for the post\'s ready status to be \'FINISHED\'' if post_debug.json()['status'] != 'FINISHED' else ''
                logging.info(f"Post publish-ready status:: {post_debug.json()}{d_info}")
                if post_debug.json()['status'] == 'ERROR':
                    logging.error(f"Uploaded media could not be published, Error:: {post_debug.json()}")
                    return self.__tp_response_msg__(
                        message="Uploaded media could not be published", 
                        body=post_debug.json(),
                        response=post_debug,
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
                    response=publish_post,
                    is_error=True
                )

            post_debug = self.__get_uploaded_post_status__(MEDIA_CONTAINER_ID)
            if post_debug.json()['status'] != 'PUBLISHED':
                self.__delete_uploaded_files__(files=self.__handled_media__)
                delete_gh_files = False
                logging.error(f"Post not sent, Error message {post_debug.json()['error_message']}")
                return self.__tp_response_msg__(
                    message=f"Post not sent, Error message {post_debug.json()['error_message']}", 
                    body=post_debug,
                    response=post_debug,
                    is_error=True
                )

            return {'id': publish_post.json()['id'], 'publish_post': publish_post}
        
        except Exception as e:
            debug = {}
            if delete_gh_files:
                self.__delete_uploaded_files__(files=self.__handled_media__)  

            if len(medias) > 0:
                debug = self.__get_uploaded_post_status__(MEDIA_CONTAINER_ID)
            
            r_debug = debug
            debug = debug.json() if type(debug) is requests.Response else debug

            logging.error(f"Could not send post")
            logging.error(f"Exception: {e}")
            if len(debug.keys()) > 0:
                logging.error(f"Published Post Debug: {debug}")

            return self.__tp_response_msg__(
                message=f"An unknown error occured could not send post", 
                body=debug | {'e': e},
                response=r_debug,
                is_error=True
            )
    
    def __get_uploaded_post_status__(self, media_id: int):
        """
            ### ThreadsPipe.__get_uploaded_post_status__

            #### Description
            The method to provide information on the status of post and media item/file upload
        """
        
        
        media_debug_endpoint = f"https://graph.threads.net/{self.__threads_api_version__}/{media_id}?fields=status,error_message&access_token={self.__threads_access_token__}"
        req_debug_response = requests.get(media_debug_endpoint)
        return req_debug_response
    
    def __split_post__(self, post: str, tags: List) -> List[str]:
        if len(post) <= self.__threads_post_length_limit__:
            first_tag = "" if len(tags) == 0 else "\n"+tags[0].strip()
            first_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post) else first_tag
            return [post + first_tag]
        
        tagged_post = []
        untagged_post = []

        clip_tags = tags[:math.ceil(len(post) / self.__threads_post_length_limit__)]

        prev_strip = 0
        tagged_striped_text = ""
        for i in range(len(clip_tags)):
            _tag = "\n"+clip_tags[i].strip()
            extra_strip = 3 if i == 0 else 6
            prev_tag = len("\n"+clip_tags[i - 1].strip()) + extra_strip if i > 0 else len("\n"+clip_tags[i].strip()) + extra_strip
            pre_dots = "" if i == 0 else "..."
            sub_dots = "..." if i + 1 < len(clip_tags) or (self.__threads_post_length_limit__ * (i + 1)) < len(post) else ""
            put_tag = "" if self.__auto_handle_hashtags__ and not self.__should_handle_hash_tags__(post[(self.__threads_post_length_limit__ * i) : (self.__threads_post_length_limit__ * (i+1))]) else _tag
            start_strip = prev_tag
            stripped_text = post[(self.__threads_post_length_limit__ * i) - prev_strip : (self.__threads_post_length_limit__ * (i + 1)) - (extra_strip + prev_strip + len(put_tag))]
            tagged_striped_text += stripped_text
            _post = pre_dots + stripped_text + sub_dots + put_tag
            prev_strip = (extra_strip + prev_strip + len(put_tag))
            tagged_post.append(_post)
        
        has_more_text = len(''.join(tagged_post)) < len(post)

        extra_text = post[len(tagged_striped_text):]

        if has_more_text:
            text_split_range = math.ceil(len(extra_text)/self.__threads_post_length_limit__)
            start_strip = 0
            for i in range(text_split_range):
                extra_strip = 3 if i == 0 and len(tagged_post) == 0 else 6
                pre_dots = "" if i == 0 and len(tagged_post) == 0 else "..."
                sub_dots = "..." if i + 1 < text_split_range else ""
                _post = pre_dots + extra_text[(self.__threads_post_length_limit__ * i) - start_strip : (self.__threads_post_length_limit__ * (i + 1)) - (extra_strip + start_strip)] + sub_dots
                start_strip = (extra_strip + start_strip)
                untagged_post.append(_post)

        return tagged_post + untagged_post
        

    def __should_handle_hash_tags__ (self, post: Union[None, str]):
        if post == None:
            return False
        return len(re.compile(r"([\w\s]+)?(\#\w+)\s?\w+").findall(post)) == 0 if self.__auto_handle_hashtags__ == True else self.__handle_hashtags__

    @staticmethod
    def __quote_str__(text: str):
        return urlp.quote(text)
    
    @staticmethod
    def __rand_str__(length: int):
        characters = string.ascii_letters + string.digits
        random_string = ''.join(random.choice(characters) for _ in range(length))
        return random_string
    
    @staticmethod
    def __is_base64__(o_str: str):
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
            if type(file) == str and self.__file_url_reg__.fullmatch(file):
                has_ext_reg = re.compile(r"\.(?P<ext>[a-zA-Z0-9]+)$").search(file)
                media_type = None
                if has_ext_reg != None:
                    media_type = filetype.get_type(ext=has_ext_reg.group('ext'))
                    media_type = None if media_type is None else media_type.mime
                
                if has_ext_reg is None or media_type is None:
                    file_url = 'http://' + file if urlp.urlparse(file).scheme == '' else file
                    req_check_type = requests.head(file_url)
                    if req_check_type.status_code > 200:
                        self.__delete_uploaded_files__(files=self.__handled_media__)
                        logging.error(f"File at index {media_files.index(file)} could not be found so its type could not be determined")
                        return self.__tp_response_msg__(
                            message=f"File at index {media_files.index(file)} could not be found so its type could not be determined", 
                            body={},
                            is_error=True
                        )
                    media_type = req_check_type.headers['Content-Type']

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
                # continue
            elif self.__is_base64__(file):
                _file = self.__get_file_url__(base64.b64decode(file), media_files.index(file))
                if 'error' in _file:
                    return _file
                self.__handled_media__.append(_file)
            elif type(file) == bytes or os.path.exists(file):
                _file = self.__get_file_url__(file, media_files.index(file))
                if 'error' in _file:
                    return _file
                self.__handled_media__.append(_file)
            else:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                logging.error(f"Provided file at index {media_files.index(file)} is invalid")
                return self.__tp_response_msg__(
                    message=f"Provided file at index {media_files.index(file)} is invalid", 
                    body={},
                    is_error=True
                )


        return self.__handled_media__
    
    def __get_file_url__(self, file: Any, file_index: int):
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

            if req_upload_file.status_code > 201:
                self.__delete_uploaded_files__(files=self.__handled_media__)
                logging.error(f"An unknown error occured while trying to upload local file at index {file_index} to GitHub")
                return self.__tp_response_msg__(
                    message=f"An unknown error occured while trying to upload local file at index {file_index} to GitHub", 
                    body=req_upload_file.json(),
                    response=req_upload_file,
                    is_error=True
                )
            
            response = req_upload_file.json()
            file_obj['url'] = response['content']['download_url']
            file_obj['sha'] = response['content']['sha']
            file_obj['_link'] = response['content']['_links']['self']

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
            finally:
                self.__handled_media__ = []
                
    
    @staticmethod
    def __tp_response_msg__(message: str, body: Any, response: Any = None, is_error: bool = False):
        _request = {'response': response} if response is not None else {}
        return ({'info': 'error', 'error': body } if is_error else {'info': 'success', 'data': body }) | { 'message': message } | _request
    
