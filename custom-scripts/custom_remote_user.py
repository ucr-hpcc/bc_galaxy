"""
Middleware for handling $REMOTE_USER if use_remote_user is enabled.
"""

import logging
import socket

from galaxy.util import safe_str_cmp

log = logging.getLogger(__name__)

#Used to get running Galaxy instance and user objects
from galaxy.webapps.galaxy.api import get_app
from galaxy.managers.users import UserManager

"""
TODO: 
    Finish Galaxy Auth
        * Auth for admin users (might be multiple admin users)
        * Auth for regular users (use UserManager class but in future might wanna use sqlite tools to access database directly)

"""

errorpage = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
    <head>
        <title>Galaxy</title>
        <style type="text/css">
        body {
            min-width: 500px;
            text-align: center;
        }
        .errormessage {
            font: 75%% verdana, "Bitstream Vera Sans", geneva, arial, helvetica, helve, sans-serif;
            padding: 10px;
            margin: 100px auto;
            min-height: 32px;
            max-width: 500px;
            border: 1px solid #AA6666;
            background-color: #FFCCCC;
            text-align: left;
        }
        </style>
    </head>
    <body>
        <div class="errormessage">
            <h4>%s</h4>
            <p>%s</p>
        </div>
    </body>
</html>
"""


class RemoteUser:

    def __init__(
        self,
        app,
        maildomain=None,
        display_servers=None,
        admin_users=None,
        single_user=None,
        remote_user_header=None,
        remote_user_secret_header=None,
        normalize_remote_user_email=False,
    ):
        self.app = app
        self.maildomain = maildomain
        self.display_servers = display_servers or []
        self.admin_users = admin_users or []
        self.remote_user_header = remote_user_header or "HTTP_REMOTE_USER"
        self.single_user = single_user
        self.config_secret_header = remote_user_secret_header
        self.normalize_remote_user_email = normalize_remote_user_email

    def __call__(self, environ, start_response):
        # Allow display servers

        log.debug(self.display_servers)
        if self.display_servers and "REMOTE_ADDR" in environ:
            try:
                host = socket.gethostbyaddr(environ["REMOTE_ADDR"])[0]
            except (OSError, socket.herror, socket.gaierror, socket.timeout):
                # in the event of a lookup failure, deny access
                host = None
            if host in self.display_servers:
                environ[self.remote_user_header] = "remote_display_server@%s" % (self.maildomain or "example.org")
                return self.app(environ, start_response)

        if self.single_user:
            assert self.remote_user_header not in environ
            environ[self.remote_user_header] = self.single_user
    

        if environ.get(self.remote_user_header, "").startswith("(null)"):
            # Throw away garbage headers.
            # Apache sets REMOTE_USER to the string '(null)' when using the
            # Rewrite* method for passing REMOTE_USER and a user is not authenticated.
            # Any other possible values need to go here as well.
            log.debug(
                "Discarding invalid remote user header %s:%s.",
                self.remote_user_header,
                environ.get(self.remote_user_header, None),
            )
            environ.pop(self.remote_user_header)
        if self.remote_user_header in environ:
            # process remote user with configuration options.
            if self.normalize_remote_user_email:
                environ[self.remote_user_header] = environ[self.remote_user_header].lower()
            if self.maildomain and "@" not in environ[self.remote_user_header]:
                environ[self.remote_user_header] = f"{environ[self.remote_user_header]}@{self.maildomain}"

           #Verify remote user 
            environ[self.remote_user_header] = self.verify_user(environ[self.remote_user_header], environ)
            
            #Display custom message if remote user is not in the database
            if environ[self.remote_user_header] == None:
                log.debug(f"Unable to identify user.  {environ[self.remote_user_header]} not found")
                for k, v in environ.items():
                    log.debug("%s = %s", k, v)

                title = "Access to Galaxy is denied"
                message = """
                        Galaxy is configured to authenticate users via a custom method
                        developed by the UCR HPCC team. If you believe this is an error please submit a support ticket at support@hpcc.ucr.edu</p>
                        """
                return self.error(start_response,title, message)

        path_info = environ.get("PATH_INFO", "")

        # The API handles its own authentication via keys
        # Check for API key before checking for header
        if path_info.startswith("/api/"):
            return self.app(environ, start_response)

        # If the secret header is enabled, we expect upstream to send along some key
        # in HTTP_GX_SECRET, so we'll need to compare that here to the correct value
        #
        # This is not an ideal location for this function.  The reason being
        # that because this check is done BEFORE the REMOTE_USER check,  it is
        # possible to attack the GX_SECRET key without having correct
        # credentials. However, that's why it's not "ideal", but it is "good
        # enough". The only users able to exploit this are ones with access to
        # the local system (unless Galaxy is listening on 0.0.0.0....). It
        # seems improbable that an attacker with access to the server hosting
        # Galaxy would not have access to Galaxy itself, and be attempting to
        # attack the system
        if self.config_secret_header is not None:
            if environ.get("HTTP_GX_SECRET") is None:
                title = "Access to Galaxy is denied"
                message = """
                Galaxy is configured to authenticate users via an external
                method (such as HTTP authentication in Apache), but
                no shared secret key was provided by the
                upstream (proxy) server.</p>
                <p>Please contact your local Galaxy administrator.  The
                variable <code>remote_user_secret</code> and
                <code>GX_SECRET</code> header must be set before you may
                access Galaxy.
                """
                return self.error(start_response, title, message)
            if not safe_str_cmp(environ.get("HTTP_GX_SECRET", ""), self.config_secret_header):
                title = "Access to Galaxy is denied"
                message = """
                Galaxy is configured to authenticate users via an external
                method (such as HTTP authentication in Apache), but an
                incorrect shared secret key was provided by the
                upstream (proxy) server.</p>
                <p>Please contact your local Galaxy administrator.  The
                variable <code>remote_user_secret</code> and
                <code>GX_SECRET</code> header must be set before you may
                access Galaxy.
                """
                return self.error(start_response, title, message)

        if environ.get(self.remote_user_header, None):
            if not environ[self.remote_user_header].count("@"):
                if self.maildomain is not None:
                    environ[self.remote_user_header] += f"@{self.maildomain}"
                else:
                    title = "Access to Galaxy is denied"
                    message = """
                        Galaxy is configured to authenticate users via an external
                        method (such as HTTP authentication in Apache), but only a
                        username (not an email address) was provided by the
                        upstream (proxy) server.  Since Galaxy usernames are email
                        addresses, a default mail domain must be set.</p>
                        <p>Please contact your local Galaxy administrator.  The
                        variable <code>remote_user_maildomain</code> must be set
                        before you may access Galaxy.
                    """
                    return self.error(start_response, title, message)
            user_accessible_paths = (
                "/users",
                "/user/api_key",
                "/user/edit_username",
                "/user/dbkeys",
                "/user/logout",
                "/user/toolbox_filters",
                "/user/set_default_permissions",
            )

            admin_accessible_paths = (
                "/user/create",
                "/user/logout",
                "/user/manage_user_info",
                "/user/edit_info",
            )

            if not path_info.startswith("/user"):
                # shortcut the following allowlist for non-user-controller
                # requests.
                pass
            elif environ[self.remote_user_header] in self.admin_users and any(
                path_info.startswith(prefix) for prefix in admin_accessible_paths
            ):
                # If the user is an admin user, and any of the admin accessible paths match..., allow them to execute that action.
                pass
            elif any(path_info.startswith(prefix) for prefix in user_accessible_paths):
                # If the user is allowed to access the path, pass
                pass
            elif path_info == "/user" or path_info == "/user/":
                pass  # We do allow access to the root user preferences page.
            elif path_info.startswith("/user"):
                # Any other endpoint in the user controller is off limits
                title = "Access to Galaxy user controls is disabled"
                message = """
                    User controls are disabled when Galaxy is configured
                    for external authentication.
                """
                return self.error(start_response, title, message)

            return self.app(environ, start_response)
        else:
            log.debug(f"Unable to identify user.  {self.remote_user_header} not found")
            for k, v in environ.items():
                log.debug("%s = %s", k, v)

            title = "Access to Galaxy is denied"
            message = """
                Galaxy is configured to authenticate users via an external
                method (such as HTTP authentication in Apache), but a username
                was not provided by the upstream (proxy) server.  This is
                generally due to a misconfiguration in the upstream server.</p>
                <p>Please contact your local Galaxy administrator.
            """
            return self.error(start_response, title, message)

    def verify_user(self, user_name, environ):
        #Should probably change to use sqlite tools to access user info from database
        galaxy_user_manager = get_app().user_manager

        if self.admin_users is not None:

            #https://stackoverflow.com/questions/16380326/check-if-substring-is-in-a-list-of-strings
            admin_list = '\t'.join(self.admin_users)
            
            if user_name in admin_list: 
            
            #Galaxy user is an admin user
            #1.) Find admin user corresponding to user
            #2.) Check if admin user exists within database
                # * Create user (by appending email address from admin_user)
                # * Or might need to set default maildomain

                #This should loop through the admin list and find the admin user corresponding to the 
                #user passed in through header
                
                for i in range(len(self.admin_users)):
                    if user_name == self.admin_users[i].split('@')[0]:
                        admin_user = galaxy_user_manager.get_user_by_identity(self.admin_users[i].split('@')[0])
                        return self.admin_users[i]         
        
        regular_galaxy_user = galaxy_user_manager.get_user_by_identity(user_name)
        if regular_galaxy_user != None and regular_galaxy_user.deleted == False:
            regular_galaxy_user = f"{regular_galaxy_user.email}"
            return regular_galaxy_user

        return None

    def error(self, start_response, title="Access denied", message="Please contact your local Galaxy administrator."):
        start_response("403 Forbidden", [("Content-type", "text/html")])
        return [errorpage % (title, message)]
