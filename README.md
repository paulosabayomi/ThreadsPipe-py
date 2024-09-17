# ThreadsPipePy

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->
[![MIT License](https://img.shields.io/github/license/paulosabayomi/ThreadsPipe-py?style=flat-square)](https://github.com/paulosabayomi/ThreadsPipe-py/blob/main/LICENSE)
[![Language](https://img.shields.io/badge/language-Python-yellow.svg?style=flat-square&logo=python)](https://www.python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg?style=flat-square)](https://github.com/paulosabayomi/ThreadsPipe-py/pulls)
[![Repository](https://img.shields.io/static/v1?label=&labelColor=505050&message=Repository&color=0076D6&style=flat-square&logo=github&logoColor=0076D6)](https://github.com/marketplace/actions/ThreadsPipe-py)
[![Tests & lint for v3.8 - v3.11](https://github.com/paulosabayomi/ThreadsPipe-py/actions/workflows/python-package.yml/badge.svg)](https://github.com/paulosabayomi/ThreadsPipe-py/actions/workflows/python-package.yml)
[![Publish to Pypi](https://github.com/paulosabayomi/ThreadsPipe-py/actions/workflows/python-publish.yml/badge.svg)](https://github.com/paulosabayomi/ThreadsPipe-py/actions/workflows/python-publish.yml)
<!-- [END BADGES] -->

threadspipepy Python library uses the official Meta's Threads API to perform actions on a user's account, actions like create post, respond to posts and replies, get posts and user's account insights and many more.
  
## Instalation
  
Installation requires at least Python 3.8  
  
```bash
pip install threadspipepy
# OR
# pip3 install threadspipepy
```

If you want to add the dependencies required for the threadspipepy CLI, install ThreadsPipe with

```bash
pip install threadspipepy[cli]
# OR
# pip3 install threadspipepy[cli]
```

This will install ThreadsPipePy, the dependencies and the CLI dependencies

## Setup

To get started you need Facebook developer account, head over to [https://developers.facebook.com/apps](https://developers.facebook.com/apps) to create an account and then create an app with the Threads Use Case, follow this guide to complete your app setup [https://developers.facebook.com/docs/development/create-an-app/threads-use-case](https://developers.facebook.com/docs/development/create-an-app/threads-use-case).
  
After creating an app with Threads use case and selecting the permissions you need, you can start using ThreadsPipe.  

### Getting started

#### Authorization window - first step

The next thing is to implement the Authorization window to get the authorization token which will be swapped for the short and long lived access tokens, after the user has granted your app access they will be redirected to your redirect_uri page in which the authorization token will be in the `code` parameter added as a query string to the redirect_uri, so for example if passed a redirect_uri like `https://example.com/handler.php` when the user gets redirected to the uri the resulting uri will be like `https://example.com/handler.php?code=Abcdef...#_` and notice the `#_` at the end of the token which needs to be stripped off.  

When you call the `api.get_auth_token` method below it will open the device's default browser and open up the authorization window/page which is something that will look like this  
![https://scontent-los2-1.xx.fbcdn.net/v/t39.8562-6/448400385_1192671258431902_561156009842405502_n.png?_nc_cat=103&ccb=1-7&_nc_sid=f537c7&_nc_eui2=AeGrI_W3z9vLHWDV0HS-0uYc-hVBpkMYS7r6FUGmQxhLuhjqStbGD39iw-kDPd0sCZzHLFF8iggafsW4sc7l_1Mn&_nc_ohc=VjSWy68S8iUQ7kNvgGSm4e3&_nc_ht=scontent-los2-1.xx&_nc_gid=A8r71txUnRNcBuoYzFFanrz&oh=00_AYCCa4mRKAh5NGn8v_P7ONZR0E-xPY3vM-U6zdlWrOixIw&oe=66EA2CCF](https://scontent-los2-1.xx.fbcdn.net/v/t39.8562-6/448400385_1192671258431902_561156009842405502_n.png?_nc_cat=103&ccb=1-7&_nc_sid=f537c7&_nc_eui2=AeGrI_W3z9vLHWDV0HS-0uYc-hVBpkMYS7r6FUGmQxhLuhjqStbGD39iw-kDPd0sCZzHLFF8iggafsW4sc7l_1Mn&_nc_ohc=VjSWy68S8iUQ7kNvgGSm4e3&_nc_ht=scontent-los2-1.xx&_nc_gid=A8r71txUnRNcBuoYzFFanrz&oh=00_AYCCa4mRKAh5NGn8v_P7ONZR0E-xPY3vM-U6zdlWrOixIw&oe=66EA2CCF)  
  
To implement the Authorization window:

```py
from threadspipepy.threadspipe import ThreadsPipe

api = ThreadsPipe(
    access_token='for now leave this as an empty string we will update it later below', # read more below on how to get your long lived or short lived access token
    user_id='also leave this as an empty string we will update it later below', # The user_id of the Threads account, read more below
    handle_hashtags=True, # read more on handle_hashtags below
    auto_handle_hashtags=False, # read more on auto_handle_hashtags below
    # gh_bearer_token = 'github-fined-grain-token',
    # gh_repo_name = 'the-repository-for-temporary-file-upload',
    # gh_username = 'your-github-username',
    # ... read more on other parameters below
)

auth_code = api.get_auth_token(
    app_id= 'your-app-id', # your app id in app-dashboard > use cases > Customize > Settings
    redirect_uri='https://example.com/handler.php',
    scope='all' # the optional scope or permissions that you allowed in your app read more on this in the `get_auth_token` method below
)

print("token", token)
```
  
To get a list of all `scope`s that can be passed to the `get_auth_token` method, get it from the `ThreadsPipe.__threads_auth_scope__.keys()` or `api.__threads_auth_scope__.keys()` this will list out all of the possible values of scopes that you can pass to the `scope` parameter.  
  
This will open the Threads authorization window/web page and the user will be asked to grant your app access (might also be required to sign in if not signed in), then the user will be redirected to your redirect_uri after granting or rejecting the permission, if the user grants your app the permission then the authorization code will be in the redirect uri as mentioned above.  
  
Then after getting the authorization code, it's time to swap it for both short and long lived access tokens, don't worry ThreadsPipe will generate both for you at once, the short lived access token is only valid for 1 hour and the long lived access token for 60 days. To get both tokens:

```py
tokens = api.get_access_tokens(
    app_id='same-app-id',
    app_secret='your-app-secret', # you can get it on the same page as your app_id
    auth_code=auth_code, # the authorization code gotten from the redirect_uri passed to the authorization window above
    redirect_uri='https://example.com/handler.php', # must be the same redirect_uri as the one used when requesting for the authorization code
)

print("access_token", tokens)
```

Then this will return the `user_id`, the short and long lived access tokens, then you are ready to start making requests, you can then update the access_token and user_id parameters in ThreadsPipe, to update these parameters simply call the `ThreadsPipe.update_param`, the method can update any parameters that can be passed to the `threadspipe.ThreadsPipe` object, example

```py
api.update_param(
    user_id=tokens['user_id'],
    access_token=tokens['tokens']['long_lived']['access_token'], # long lived access tokens is recommended
)
```
  
Then you can make your first request, by posting a content to Threads

### Basic Usage

```py

pipe = api.pipe(
    post="A very long text...",
    files=[
        # "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/BigBuckBunny.jpg",
        # bs4_img,
        # open('test.gif', 'rb').read(),
        # "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "./img-2.jpg",
        "https://images.unsplash.com/photo-1482062364825-616fd23b8fc1?q=80&w=2370&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        open('img-1.jpg', 'rb').read(),
        "https://images.unsplash.com/photo-1504639725590-34d0984388bd?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        open('sample-5.mp4', 'rb').read(),
        "https://images.unsplash.com/photo-1721332149371-fa99da451baa?q=80&w=2536&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        "https://images.unsplash.com/photo-1725554515068-8bb766ba0724?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwxMnx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725647093138-e1ef909ca53c?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwxNnx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725489890999-84e4f2f71327?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725829879131-1780c5291059?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725628736546-6b334a2002d7?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725714355497-a4da39972ef2?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzMnx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725792630033-e462b10672ec?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzNnx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1724764147620-598dd5356fd7?q=80&w=2574&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        "https://images.unsplash.com/photo-1725462567088-0898ef927c8d?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHw0MHx8fGVufDB8fHx8fA%3D%3D"
    ],
    allowed_country_codes="US,CA,NG" # the user needs to have the geo-gating permission to use this feature read more below

    # read more below on file captions
    file_captions=['image of a macbook on a white table', "image 1 from unsplash", "coding picture taken upclose", None, "video of watering a garden flower", None, None, None, None, "Image second from Unsplash", None, None, "Another third image from Unsplash", None, "Image 4 from Unsplash", None, "Image 5 from unsplash", None], 
    who_can_reply="accounts_you_follow"
)

print("pipe", pipe)
```

The length of the `post` can be more than the limit which is currently 500 characters and / or the number of files can be more than the limit per post which is 10 files per post and in that case ThreadsPipe will split the post into a 'X(fka Twitter)-like thread' post or simply the post will be chained together, if the post has text longer than 500 and images more than 10, both will be splitted into batches and the first batches of both the files and text content will be the main/root post and the following batches will be like a reply to the first post creating something like a thread on X(fka Twitter) or a chained post.  
  
### Uploading locally available files to Threads

By default Threads only allows providing the links to files that are on a public server for upload, but to fix this issue ThreadsPipe is going to upload your local files to GitHub first, get their download links and provide them to Threads, and then delete them immediately after sending the post or if it encountered an error and couldn't publish the post, all you need to do is to create a github repository where ThreadsPipe will be uploading the local files to, then create a fine-grained access token at [https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta), then provide your github username, you will be passing these data to the ThreadsPipe class upon initialization or use the `ThreadsPipe.update_param` to update the github parameters needed for the temporary file upload to GitHub else you will get an error when you try to upload local files, example below

```py
api = ThreadsPipe(
    access_token=access_token, # read more below on how to get your long lived or short lived access token
    user_id=user_id, # The user_id of the Threads account, read more below
    handle_hashtags=True, # read more on handle_hashtags below
    auto_handle_hashtags=False, # read more on auto_handle_hashtags below
    gh_bearer_token = 'github-fined-grain-token',
    gh_repo_name = 'threadspipe-uploads',
    gh_username = 'example',
)

# OR
api.update_param(
    gh_bearer_token = 'github-fined-grain-token',
    gh_repo_name = 'threadspipe-uploads',
    gh_username = 'example',
)
```
  
### Using the ThreadsPipe CLI

With the ThreadsPipe CLI you can get access tokens (short and long lived) and you can also refresh the long lived access token before it expires. To use the CLI you can install ThreadsPipe with the `pip install threadspipepy[cli]` command and it will either only install the dependencies requires for the CLI if you already have ThreadsPipe installed or install the CLI dependencies along with the ThreadsPipe installation.  
  
#### To generate short and long lived access tokens on the CLI

To generated short and long lived access tokens, I will assume you have already gotten the authorization code, if yes then the command is as follows:

```bash
threadspipepy access_token --app_id=your-app-id --auth_code="the-auth-code" --app_secret="your-app-secret" --redirect_uri='https://redirect-uri.com/redirect' --env_path="./.env" --env_variable=long_lived_token_variable
```

The command will generate access tokens by swapping the authorization code for both short and long lived access tokens and this can also be achieved by calling the `ThreadsPipe.get_access_tokens` method, all the optional arguments are required and only the `--env_path` and `--env_variable` arguments are optional, set both the `--env_path` and `--env_variable` arguments if you want to automatically update an environment variable with the generated long lived access token, more details below.  
  
#### To refresh long lived access token on the CLI
  
Only long lived access token can be refreshed, short lived access token can not be refreshed after it has expired, long lived access token expires after 60 days and you can refresh them after they are at least 24 hours old, so to refresh the long lived token with the ThreadsPipe CLI, this can also be done with the `refresh_token` method, run the commands below:

```bash
threadspipepy refresh_token --access_token="your-unexpired-long-lived-access-token" --env_path="./.env" --env_variable="acc_tkn"
```

This will refresh the long lived access token and then automatically update the provided environment variable with the newly generate long lived token, but the  `--env_path` and `--env_variable` arguments are optional, there are also additional 2 options that can be passed in which the later will also work for access tokens generation above, `--auto_mode=true` and `--silent=true`, if the `--auto_mode` is set to `true` e.g. `... --auto_mode=true` then the `--env_path` and `--env_variable` arguments will be required to be set for this operation and the `--access_token` argument will be ignored and the value of the `--env_variable` in the provided `.env` file will be used in making the refresh token request and then will also be automatically updated with the newly generated long lived access token. see below for more explanations, use the `--silent=true` or just `-s` if you want to disable logging.  
  
Type `threadspipepy -h` in the terminal for help and more details of ThreadsPipe CLI usage. You can also read more on the commands below.  
  
Read more below.  
  
## Class Object, properties and methods
  
### Methods
  
- ThreadsPipe.update_param  
To update the default class parameters, it is not guaranteed that the updated value of the parameter(s) will be used if this method is called before performing an action with the parameter(s) that was set with the method, so it is recommended to call this method to set the parameter(s) before performing the action(s) with the parameter(s) that was set.
  
- ThreadsPipe.pipe  
The pipe method is for sending posts and replies to Threads.  
  
- ThreadsPipe.get_quota_usage  
The method to get user's quota usage.  
  
- ThreadsPipe.get_auth_token  
Use this method to implement the Authorization Window, The Authorization Window
allows your app to get authorization codes and permissions from app users.
Authorization codes can be exchanged for Threads user access tokens, which must be included when fetching an app user's profile, retrieving Threads media, publishing posts, reading replies, managing replies, or viewing insights.  
  
- ThreadsPipe.get_access_tokens  
This method swaps the access token gotten from Authorization Window for short and long lived access token.  
  
- ThreadsPipe.refresh_token  
Use this method to refresh unexpired long lived access tokens before they expire, long lived access tokens expire after 60 days, and you can only refresh long lived token and anytime after it is at least 24 hours old.  
  
- ThreadsPipe.is_eligible_for_geo_gating  
Use this method to check for an account's eligibility for posting geo-gated contents.  
  
- ThreadsPipe.get_allowlisted_country_codes  
Use this method to get a list of the country code values that can be used to limit geo-gating contents.  
  
- ThreadsPipe.get_posts  
This method returns all the posts an account has posted including the replies.  
  
- ThreadsPipe.get_post  
This method returns the data of a single post.  
  
- ThreadsPipe.get_profile  
The method to get user profile.  
  
- ThreadsPipe.get_post_replies  
The method to get post replies.  
  
- ThreadsPipe.get_user_replies  
The method to get all user's replies.  
  
- ThreadsPipe.hide_reply  
The method to hide a reply under a user's post.  
  
- ThreadsPipe.get_post_insights
The method to get post insights, like number of like, view and so on.  
  
- ThreadsPipe.get_user_insights  
The method to get user's account insights.  
  
- ThreadsPipe.get_post_intent  
The method to get Threads' post intent.  
  
- ThreadsPipe.get_follow_intent  
The method to get the follow intent link, this intents allow people to easily follow a Threads account directly from your website.  
  
### Properties
  
- `ThreadsPipe.__threads_auth_scope__`  
  
- ThreadsPipe.threads_post_insight_metrics  
  
- ThreadsPipe.threads_user_insight_metrics  
  
- ThreadsPipe.threads_follower_demographic_breakdown_list  
  
- ThreadsPipe.who_can_reply_list  
  
### ThreadsPipe class
  
```py
api = ThreadsPipe(
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
)
```
  
**Example**  
  
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
  
- Parameters  
  
*user_id*: `int`  The user_id of the Threads account, which is part of the data returned when you call the `get_access_tokens` method.  
  
*access_token*: `str` The user's account access token, either the short or long lived access token can be used, but the long lived access token is recommended, the short and long lived access token are part of the data returned when you call the `get_access_tokens` method.  
  
*disable_logging* - `bool | False` By default ThreadsPipe displays logs using the python's `logging` module, if you want to disable logging set this to `False`  
  
*wait_before_post_publish*: `bool | True` It is recommended to wait for the status of media items (or uploaded files) or media containers (post blueprints) to be 'FINISHED' before publishing a Threads media container, the average wait time is 30 seconds and trying to publish a media item/file, and media container / post before it has finished processing could cause the publishing of the media container/post to fail, it is recommended to leave this parameter to `True`.  
  
*post_publish_wait_time*: `int | 35` The time to wait for a media container or post in seconds to finish processing before publishing it.  
**Note:** it must not be less than 30 seconds and it is recommended not to be less than 31 seconds.  
  
*wait_before_media_item_publish*: `bool | True` Media item (AKA uploaded files), just like media containers/posts, it is also recommended to wait for media items or uploaded files to finish processing before publishing the media container or post it is attached to.  
  
*media_item_publish_wait_time*: `int | 35` The time to wait for a media item/uploaded files to finish processing, different media item types have different processing time and image files with small file sizes are always processed quickly than ones with larger file sizes and video files.  
  
*handle_hashtags*: `bool | True` ThreadsPipe automatically handle hastags that are added to the end of a post, because only one hashtag is allowed in a threads post, so the tags are extracted and splitted and added to each of the chained posts, To not automatically handle hashtags set this to `False` if the text in the post is longer than the maximum character allowed by threads for a post or the provided files are more than the maximum allowed the post will be splitted and chained to the root post which is going to be like a thread post on X. The body of the post might already have an hashtag to make it more dynamic set the `auto_handle_hashtags` to `True`, when `auto_handle_hashtags` is `True` the post body that already has an hashtag will be skipped and no hashtag will be added to it.  
  
*auto_handle_hashtags*: `bool | False` When this is `True` it will more intelligently (that what the `handle_hashtags` option does) and automatically handle hashtags, in cases where there are many hashtags at the end of a posts, the hashtags will be extracted and distributed intelligently between the chained posts, posts that already have an hashtag within the body of the post will not be given an hashtag.  
  
*gh_bearer_token*: `str | None` Your GitHub fine-grained token, which can be gotten from [https://github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta), Because to upload files to the Threads API, only the url to the files are allowed and the files must be on a public server, and this is going to be challenging when uploading files available locally on your computer or local files on a server that are not exposed to the public, that's why ThreadsPipe will first of all upload the local files in the provided files to GitHub and then delete them after the files are uploaded to Threads or if an error occured while trying to publish the post.  
  
*gh_api_version*: `str | '2022-11-28'` The GitHub API version.  
  
*gh_repo_name*: `str | None` The name of the repository that should be used for the temporary storage of the local files.  
  
*gh_username*: `str | None` Your GitHub username.  
  
*gh_upload_timeout*: `int` The upload timeout of the local files to GitHub, the default is `60 * 5` (5 minutes), but you can either reduce it or increase it.  
  
*wait_on_rate_limit*: `bool | False` Whether ThreadsPipe should wait when rate limit is hit instead of rejecting the request, this can have an impact on the memory on your server in scenarios where multiple requests are made and will spawn multiple waiting processes.  
  
*check_rate_limit_before_post*: `bool | True` By default ThreadsPipe checks rate limit everytime before proceeding to post, if you don't want it to perform the check you can set it to `False`.  
  
*threads_api_version*: `str | 'v1.0'` Set this parameter to the Meta's Threads API version you want to use, default is `v1.0`.
  
### ThreadsPipe.pipe
  
- Description  
The pipe method is for sending posts and replies to Threads, you can also make geo-gated post and replies which requires the user to have the geo-gating permission.  
  
```py
api.pipe(
    post: Optional[str] = "", 
    files: Optional[List] = [], 
    file_captions: List[str | None] = [],
    tags: Optional[List] = [],
    reply_to_id: Optional[str] = None, 
    who_can_reply: str | None = None,
    chained_post = True, 
    persist_tags_multipost = False,
    allowed_country_codes: str | List[str] = None,
)
```
  
**Example**  
  
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
  
**Parameters**  
*post*: `str | ""` This parameter takes a string which is the text content of the post, it can be of any length and can be more than 500 which is the current character limit allowed in a post, ThreadsPipe will split the text into different batches of 500 characters, if the provided text is more than 500 and upload the first batch as the root post and then upload the rest of the batches as a reply to the root post, then the resulting post is going to be like an X thread post.  
  
*files*: `List | []` The media files that will be attached to the post, the allowed file types can be `bytes`, url to a file, and `base64`, you can also pass in the path to a local file, the number of files can be any length and more than 10, if the number of files is more than 10 which is the limit for a post, ThreadsPipe would split them into batches of 10 files and send the first batch with the first text batch and the rest of the batch either as replies to the root post (if the text content of the post is less than 500) or with the text batch reply(ies) to the root post.  
  
*file_captions*: `List[str | None] | []` The captions for the media files, provide the captions based on the index of the provided files and provide `None` at the index of the files that does not have caption, the length of the provided caption does not have to match the number of files provided, for example if 5 files were provided, to provided captions for files at index 1 and 4 it would be `[None, "Caption for file at index 1", None, None, "Caption for file at index 4"]`.  
  
*tags*: `List[str] | []` If you would like to provide the hashtags instead of adding them to the end of the text content, you can provide them with this property instead, they can be any length, this will have no effect if both `handle_hashtags` and `auto_handle_hashtags` are `False`, Learn more about the `handle_hashtags` and `auto_handle_hashtags` to understand them better.  
  
*reply_to_id*: `str | None` To reply to a post pass in the media id of the target post that you want to reply to, replying to a post also behaves like normal post and the text content and files will also be handled the same way.  
  
*who_can_reply*: `str | None` Use this parameter to set who can reply to the post you're sending, use the `ThreadsPipe.who_can_reply_list` property to get a list of all available options, supported options are and one of `'everyone'`, `'accounts_you_follow'`, and `'mentioned_only'`.  
  
*chained_post*: `bool | True` To turn off the automatic post chaining when the provided text content and/or the files are above the limit set this parameter to `False`.  
  
*persist_tags_multipost*: `bool | False` Set this parameter to `True` if you want either the hashtags at the end of the provided text content or the provided hashtags to not be splitted and just be added as they are, this is useful only if you are using a single hashtag and you want the hashtag to be added to each of the chained posts.  
  
*allowed_country_codes*: `List[str] | []` This requires the user to have the geo-gating permission, if you want to restrict the post to a country or a set of countries, provide the list of allowed country codes to this parameter, the format should be either a comma separated country codes i.e. "US,CA,NG" or a `List` of the allowed country codes i.e. ["US","CA","NG"], you can check if you have the permission to use the geo-gating feature by calling the `ThreadsPipe.is_eligible_for_geo_gating`.  
  
*link_attachments*: `List[str] | None` Use this to explicitly provide link(s) for the post, this will only work for text-only posts, if the number of links are more than 1 and the post was splitted into a chained post, see the `pipe` method's `post` parameter doc for more info on chained posts, then in this case because only one link is allowed per post the links will be shared among the chained posts.  
  
*Returns*  
dict | requests.Response | Response
  
### ThreadsPipe.get_quota_usage
  
- Description  
The method to get user's quota usage  
  
```py
api.get_quota_usage(for_reply=False)
```
  
**Parameters**  
*for_reply*: `bool | False` Set this parameter to `True` to get the media reply post reply quota usage, default is `False` which returns the quota usage for posts.
  
*Returns*  
requests.Response | Response | None  
  
### ThreadsPipe.get_auth_token
  
**Description**  
Use this method to implement the Authorization Window, The Authorization Window allows your app to get authorization codes and permissions from app users. Authorization codes can be exchanged for Threads user access tokens, which must be included when fetching an app user's profile, retrieving Threads media, publishing posts, reading replies, managing replies, or viewing insights.  
  
```py
api.get_auth_token(
    app_id: str, 
    redirect_uri: str, 
    scope: str | List[str] = 'all', 
    state: str | None = None
)
```
  
**Parameters**  
*app_id*: `str` Your Threads app id which can be found on the `Use cases > Customize > Settings` page.  
  
*redirect_uri*: `str` The uri that the Threads API will redirect the user to after granting or rejecting the permission request, you can provide one of the redirect uri that you listed in the Redirect Callback URLs input box, the user will be redirected to this url after the action with a `code` query parameter containing authorization token which can be used to get short and long lived access tokens. The resulting url after redirection will look like `https://example.com/api.php?code=dnsdbcbdkvv...#_` and notice the `#_` at the end of the token which is not part of the token and should be stripped off, **Note:** The authorization token can only be used once, see `get_access_tokens` method to learn more.  
  
*scope*: `str | List[str]` The scope is the Threads permissions that are enabled for the app, you can leave the value of this parameter as `all` or provide the list of comma separated string or `List` of the enabled permissions, the values should be from one of ThreadsPipe library threads-auth-scopes, which you can get by calling `ThreadsPipe.__threads_auth_scope__`, the returned dict's keys will be `basic`, `publish`, `read_replies`, `manage_replies`, `insights`.  
  
*state*: `str` The state is a code to be set to prevent CORF e.g. '1', this is *optional*  
  
*Returns*  
None
  
### ThreadsPipe.update_param
  
**Description**  
To update the default class parameters, it is not guaranteed that the updated value of the parameter(s) will be used if this method is called before performing an action with the parameter(s) that was set with the method, so it is recommended to call this method to set the parameter(s) before performing the action(s) with the parameter(s) that was set.
  
```py
api.update_param(
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
)
```
  
**Example**  
  
```py
    api.update_param(
        user_id=user_id,
        access_token=access_token,
        disable_logging=True
    )
```
  
**Parameters**  
See the `ThreadsPipe class` above for more info on the parameters.  
  
### ThreadsPipe.get_access_tokens
  
**Description**  
This method swaps the access token gotten from Authorization Window for short and long lived access token.  
  
**Example**  
  
```py
api.get_access_tokens(
    app_id: str, 
    app_secret: str, 
    auth_code: str, 
    redirect_uri: str
)
```
  
**Parameters**  
  
*app_id*: `str` The same app id you used when getting the authorization code from the authorization Window.  
  
*app_secret*: `str` This can be gotten from the `Use cases > Customize > Settings` page in the Threads App secret input box, in the app dashboard.  
  
*auth_code*: `str` The authorization code that was gotten from the redirect url of the Authorization Window, Note this code can only be used once.  
  
*redirect_uri*: `str` This redirect uri should be the same as the value of the `redirect_uri` argument passed to the `get_auth_token` method or the request will be rejected and the authorization token will be expired.  
  
*Returns*  
dict | JSON
  
### ThreadsPipe.refresh_token
  
**Description**  
Use this method to refresh unexpired long lived access tokens before they expire, long lived access tokens expire after 60 days, and you can only refresh long lived token and anytime after it is at least 24 hours old.  
  
```py
api.refresh_token(
    access_token: str, 
    env_path: str = None, 
    env_variable: str = None
)
```
  
**Parameters**  
*access_token*: `str` The long lived access token that will be refreshed for a new and life-extended one.  
  
*env_path*: `str | None` This is optional, and it is useful and only required if you want ThreadsPipe to automatically update a variable with the new long lived token access token.  
  
*env_variable*: `str | None` The name of the variable that ThreadsPipe should automatically update with the newly generated long lived access token.  
  
*Returns*  
JSON
  
### ThreadsPipe.is_eligible_for_geo_gating
  
**Description**  
Use this method to check for an account's eligibility for posting geo-gated contents.  
  
```py
api.is_eligible_for_geo_gating()
```
  
**Parameters**  
*None*
  
*Returns*  
JSON
  
### ThreadsPipe.get_allowlisted_country_codes
  
**Description**  
Use this method to get a list of the country code values that can be used to limit geo-gating contents.  
  
```py
api.get_allowlisted_country_codes(
    limit: str | int = None
):
```
  
**Parameters**  
*limit*: `str | int | None` Use this parameter to limit the amount of data returned.  
  
*Returns*  
JSON
  
### ThreadsPipe.get_posts
  
**Description**  
This method returns all the posts an account has posted including the replies.  
  
```py
api.get_posts(
    since_date: str | None = None, 
    until_date: str | None = None, 
    limit: str | int | None = None
)
```
  
**Parameters**  
*since_date*: `str | None` Set the start of the date that the posts should be returned from.  
  
*until_date*: `str | None` Set the end of the date of the posts that will be returned.  
  
*limit*: `str | int | None` The limit of the posts that should be returned.  
  
*Returns*  
JSON
  
### ThreadsPipe.get_post
  
**Description**  
This method returns the data of a single post.  
  
```py
api.get_post(post_id: str)
```
  
**Parameter**  
*post_id*: `str` The id of the post you want to get the data.  
  
*Returns*  
JSON
  
### ThreadsPipe.get_profile
  
**Description**  
The method to get user profile.  
  
```py
api.get_profile()
```
  
**Parameters**  
None  
  
*Returns*  
JSON
  
### ThreadsPipe.get_post_replies
  
**Description**  
The method to get post replies.  
  
```py
api.get_post_replies(
    post_id: str, 
    top_levels=True, 
    reverse=False
)
```
  
**Parameters**  
*post_id*: `str` The of the post you want to get its replies.  
  
*top_levels*: `bool | True` Set this parameter to `False` if you want to get the deep level or simply replies of replies of replies, by default the method get the top level replies.  
  
*reverse*: `bool | False` Set this parameter to `True` if you want the returned data to be in reverse order.  
  
*Returns*  
JSON
  
### ThreadsPipe.get_user_replies
  
**Description**  
The method to get all user's replies.  
  
```py
api.get_user_replies(
    since_date: str | None = None, 
    until_date: str | None = None, 
    limit: int | str = None
)
```
  
**Parameter**  
*since_date*: `str | None` The start of the date to return the data from.  
  
*until_date*: `str | None` The end date of the replies that will be returned.  
  
*limit*: `int | str` The limit of the data that should be returned.  
  
*Returns*  
JSON
  
### ThreadsPipe.hide_reply
  
**Description**  
The method to hide a reply under a user's post.  
  
```py
api.hide_reply(
    reply_id: str, 
    hide: bool
)
```
  
**Parameters**  
*reply_id*: `str` The id of the reply that you want to hide.  
  
*hide*: `bool` Can be `True` or `False`, set it to `True` if you want to hide the reply and `False` to unhide the reply.  
  
*Returns*  
JSON
  
### ThreadsPipe.get_post_insights
  
**Description**  
The method to get post insights, like number of like, view and so on.  
  
```py
api.get_post_insights(
    post_id: str, 
    metrics: str | List[str] = 'all'
)
```
  
**Parameters**  
*post_id*: `str` The id of the post you want to get insights for.  
  
*metrics*: `str | List[str] | 'all'` The metrics to include in the data, leave the value of this parameter as 'all' to get data for all the available metrics or pass in a list of the metrics you want either as a comma separated string or as a `List`, you can get the list of metrics you can pass from the `ThreadsPipe.threads_post_insight_metrics` parameter which are `'views'`, `'likes'`, `'replies'`, `'reposts'`, `'quotes'`.  
  
*Returns*  
JSON  
  
### ThreadsPipe.get_user_insights
  
**Description**  
The method to get user's account insights.  
  
```py
api.get_user_insights(
    user_id: str | None = None, 
    since_date: str | None = None, 
    until_date: str | None = None, 
    follower_demographic_breakdown: str = 'country', 
    metrics: str | List[str] = 'all'
)
```
  
**Parameters**  
*user_id*: `str | None` The optional user id if you want to get the account insights for another user that's different from the currently connected one to ThreadsPipe.  
  
*since_date*: `str | None` The start date that the data should be returned from, **Note:** that User insights are not guaranteed to work before June 1, 2024, and the user insights since_date and until_date parameters do not work for dates before April 13, 2024.  
  
*until_date*: `str | None` The end date of the insights data, **Note:** The user insights `since_date` and `until_date` parameters do not work for dates before April 13, 2024.  
  
*follower_demographic_breakdown*: `str | 'country'` The metrics contains the `'follower_demographics'` value which requires one follower demographic breakdown to be provided, you can get the list of all available values that you can pass to this parameter from the `ThreadsPipe.threads_follower_demographic_breakdown_list` which will return `'country'`, `'city'`, `'age'`, and `'gender'` and only one of them should be provided.  
  
*metrics*: `str | List[str] | 'all'` The metrics that should be returned for the user account's insight, you can either leave the default value of this parameter as 'all' which will return all available metrics or provide a comma separated string of the metrics you want or as a `List`, you can get the available user insight metrics from the `ThreadsPipe.threads_user_insight_metrics` which will return `"views"`, `"likes"`, `"replies"`, `"reposts"`, `"quotes"`, `"followers_count"`, and `"follower_demographics"`.  
  
**Returns**  
JSON  
  
### ThreadsPipe.get_post_intent
  
**Description**  
The method to get Threads' post intent.  
  
```py
api.get_post_intent(
    text: str = None, 
    link: str = None
)
```
  
**Parameters**  
*text*: `str | None` The text content of the post.  
  
*link*: `str | None` The link to your blog or website.  
  
*Returns*  
str  
  
### ThreadsPipe.get_follow_intent
  
**Description**  
The method to get the follow intent link, this intents allow people to easily follow a Threads account directly from your website.  
  
```py
api.get_follow_intent(
    username: str | None = None
)
```
  
**Parameters**  
*username*: `str | None` The username you want to get the follow intent for, leave this as `None` to automatically use the connected account.  
  
*Returns*  
str  
  
## ThreadsPipe CLI
  
### access_token command
  
This command will generate both short and long lived access tokens with the authorization code.  
  
| Arguments | Required | short form | Description |
| --- | --- | --- | --- |
| access_token  | `True` | *not applicable* | The positional argument to generate short and long lived access tokens from the authorization code |
| --app_id | `True` | `-id` | The same app id you used when getting the authorization code from the authorization Window. |
| --app_secret | `True` | `-secret` | Your app secret, it can be gotten from the `Use cases > Customize > Settings` page in the Threads App secret input box in the app dashboard. |
| --auth_code | `True` | `-code` | The authorization code that was gotten from the redirect url of the Authorization Window, Note this code can only be used once. |
| --redirect_uri | `True` | `-r` | This redirect uri should be the same as the value of the `redirect_uri` argument passed to the `get_auth_token` method or the request will be rejected and the authorization token will be expired. |
| --env_path | `False` | `-p` | This is optional, and it is useful and only required if you want ThreadsPipe to automatically update a variable in an .env file with the long lived token access token. |
| --env_variable | `False` | `-v` | The name of the variable that ThreadsPipe should automatically update with the long lived access token. |
| --silent | `False` | `-s` | Set this to 'true' if you want to disable logging. |  
  
### refresh_token command
  
This command will refresh your long lived access token with a new and life-extended one.  
  
| Arguments | Required | short form | Description |
| --- | --- | --- | --- |
| refresh_token | `True` | *not applicable* | The positional argument to refresh the long lived access token and returns a new and life-extended one. |
--access_token | `True` if the `--auto_mode` argument is not set and `False` if not set | `-token` | If this argument is set to 'true' when refreshing access token, the value of the env variable argument will be used in place of the --access_token option (which can be omitted in this case) to make the refresh token request and will be automatically updated with the newly generated long lived access token. |
| --auto_mode | `False` | `-auto` | If this argument is set to 'true' when refreshing access token, the value of the env variable argument will be used in place of the --access_token option (which can be omitted in this case) to make the refresh token request and will be automatically updated with the newly generated long lived access token. |
| --env_path | `True` if the `--auto_mode` argument is set and `False` if not set | `-p` | Absolute or relative path to the `.env` file, this is optional, but it is required if `--auto_mode` is set to `true` and in that case the `--access_token` argument will be ignored and the value of the `--env_variable` in the provided `.env` (which is expected to be the long lived access token) file will be used to make the refresh token refresh and then will be updated with the new and life-extended long lived access token |
| --env_variable | `True` if the `--auto_mode` argument is set and `False` if not set | `-v` | The name of the variable that ThreadsPipe should automatically update with the long lived access token. |
| --silent | `False` | `-s` | Set this to 'true' if you want to disable logging. |
  
## Inspiration
  
I got the idea when working on my Space bot which is called 'Astronomy Bot' on Threads, @astronomybot, when I faced issues like not able to post local media files to Threads and having to truncate the texts in posts to the 500-character limit which affects many posts, and then I searched for a library for Threads and that uses the official API but couldn't find and I decided to create ThreadsPipe.
  
## LICENSE

[MIT License](https://github.com/paulosabayomi/ThreadsPipepy/blob/main/LICENSE)  
  
Created with :heart: by Abayomi Amusa
