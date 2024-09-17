"""
The ThreadsPipe CLI helper, you can use this to get short and long lived access tokens 
and to refresh long lived access tokens
"""

import requests, sys, logging, pprint, argparse, os, re
from dotenv import set_key, get_key
from colorama import init, Fore, Back, Style
init()

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

def __get_access_token__(app_id: str, app_secret: str, auth_code: str, redirect_uri: str, env_path: str = None, env_variable: str = None):
        """
            ## Function __get_access_token__

            ### Description
            This function swaps the access token gotten from Authorization Window for short and long lived access token.

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
        threads_access_token_endpoint = "https://graph.threads.net/oauth/access_token"
        
        req_short_lived_access_token = requests.post(
            threads_access_token_endpoint,
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
            pprint.pp({
                "message": "Could not generate short lived token",
                "error": short_lived_token
            })
            sys.exit()
        
            

        req_long_lived_access_token = requests.get(
            f"https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret={app_secret}&access_token={short_lived_token['access_token']}"
        )

        if req_long_lived_access_token.status_code > 201:
            pprint.pp({
                "message": "Could not generate long lived token",
                "error": req_long_lived_access_token.json()
            })
            sys.exit()

        if env_path != None and env_variable != None:
            os.chdir(os.getcwd())
            set_key(env_path, env_variable, req_long_lived_access_token.json()['access_token'])
            logging.info(f"Updated the {env_variable} variable in the .env file")

        pprint.pp({
            'user_id': short_lived_token['user_id'],
            'tokens': {
                'short_lived': short_lived_token,
                'long_lived': req_long_lived_access_token.json(),
            }
        })

def __refresh_token__(access_token: str, env_path: str = None, env_variable: str = None, auto_mode:bool = None):
        """
            ## Function __refresh_token__

            ### Description
            This function refreshes unexpired long lived access tokens and returns a new and life-extended one, long \
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
        
        access_token = get_key(env_path, env_variable) if env_path != None and env_variable != None and auto_mode == True else access_token
        threads_access_token_refresh_endpoint = "https://graph.threads.net/refresh_access_token"
        refresh_token_url = threads_access_token_refresh_endpoint + f"?grant_type=th_refresh_token&access_token={access_token}"
        refresh_token = requests.get(refresh_token_url)
        if refresh_token.status_code > 201:
            return {
                'message': "An error occured could not refresh access token",
                'error': refresh_token.json()
            }
        if env_path != None and env_variable != None:
            os.chdir(os.getcwd())
            set_key(env_path, env_variable, refresh_token.json()['access_token'])
            logging.info(f"Updated the {env_variable} variable in the .env file")

        pprint.pp(refresh_token.json())

def run():
    parser = argparse.ArgumentParser(
        prog=Fore.BLUE + "ThreadsPipe CLI",
        description=Fore.GREEN + "ThreadsPipe CLI tool to get short and long lived access tokens and to refresh long lived access tokens" + Style.RESET_ALL
    )

    # get access token args
    parser.add_argument("action", help=Fore.CYAN + f"The action you want to perform: `{Fore.MAGENTA + 'access_token' + Fore.CYAN}` (to get short and long lived access tokens) or `{Fore.MAGENTA + 'refresh_token' + Fore.CYAN}` (to refresh the long lived access token)" + Style.RESET_ALL)
    parser.add_argument("-id", "--app_id", required=len(sys.argv) > 1 and sys.argv[1] == 'access_token', help=Fore.GREEN + "The same app id you used when getting the authentication code from the Authentication Window." + Style.RESET_ALL)
    parser.add_argument("-secret", "--app_secret", required=len(sys.argv) > 1 and sys.argv[1] == 'access_token', help=Fore.GREEN + "Your app secret, it can be gotten from the `Use cases > Customize > Settings` page in the Threads App secret input box, \
            in the app dashboard." + Style.RESET_ALL)
    parser.add_argument("-code", "--auth_code", required=len(sys.argv) > 1 and sys.argv[1] == 'access_token', help=Fore.GREEN + "The authentication code that was gotten from the redirect url of the Authorization Window, \
            Note this code can only be used once." + Style.RESET_ALL)
    parser.add_argument("-r", "--redirect_uri", required=len(sys.argv) > 1 and sys.argv[1] == 'access_token', help=Fore.GREEN + "This redirect uri should be the same as the value of the `redirect_uri` argument passed to the `get_auth_token` \
            method or the request will be rejected and the authorization token will be expired." + Style.RESET_ALL)

    # refresh token args
    check_for_auto_mode = re.compile(r"\-auto|\-\-auto_mode").search(" ".join(sys.argv))
    parser.add_argument('-token', '--access_token', required=False if check_for_auto_mode != None or len(sys.argv) > 1 and sys.argv[1] == 'access_token' else True, help=Fore.GREEN + "The long lived access token that will be refreshed for a new and life-extended one." + Style.RESET_ALL)
    parser.add_argument('-auto', '--auto_mode', required=False, help=Fore.GREEN + "If this argument is set to 'true' when refreshing access token, the value of the env variable argument will be used in place of the --access_token option \
                        (which can be omitted in this case) to make the refresh token request and will be automatically updated with the newly generated long lived access token" + Style.RESET_ALL)

    # general args
    parser.add_argument('-p', '--env_path', required=False if check_for_auto_mode == None else True, help=Fore.GREEN + "This is optional, and it is useful and only required if you want ThreadsPipe to automatically update a variable \
            in an .env file with the long lived token access token." + Style.RESET_ALL)
    parser.add_argument('-v', '--env_variable', required=False if check_for_auto_mode == None else True, help=Fore.GREEN + "The name of the variable that ThreadsPipe should automatically update with the \
            long lived access token." + Style.RESET_ALL)
    
    parser.add_argument('-s', '--silent', required=False, help=Fore.GREEN + "Set this to 'true' if you want to disable logging" + Style.RESET_ALL)

    if len(sys.argv) > 1:
    
        args = parser.parse_args()

        if args.silent is not None:
            logging.disable()

        if args.action not in ['access_token', 'refresh_token']:
            logging.error("Not implemented!")
            sys.exit()

        if args.env_path is not None and args.env_variable is None:
            logging.error("You must also provide the env variable")
            sys.exit()

        if args.env_variable is not None and args.env_path is None:
            logging.error("You must also provide the path to the .env file")
            sys.exit()

        if args.action == 'access_token':
            __get_access_token__(
                app_id=args.app_id, 
                app_secret=args.app_secret, 
                auth_code=args.auth_code, 
                redirect_uri=args.redirect_uri,
                env_path=args.env_path, 
                env_variable=args.env_variable
            )
        
        if args.action == 'refresh_token':
            __refresh_token__(
                access_token=args.access_token, 
                env_path=args.env_path, 
                env_variable=args.env_variable,
                auto_mode=args.auto_mode != None
            )
    else:
        parser.print_help()