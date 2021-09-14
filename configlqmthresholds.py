#!/usr/bin/env python
"""
CGNX script to configure LQM extensions on all VPNs at a site. Values provided via the CSV or via commandline

tanushree@cloudgenix.com
tkamath@paloaltonetworks.com
"""
import cloudgenix
import pandas as pd
import os
import sys
import argparse
import json

# Global Vars
SDK_VERSION = cloudgenix.version
SCRIPT_NAME = 'CloudGenix: Config SSH'
CSV_HEADER_MEDIA = ["site","latency","jitter","packetloss"]
CSV_HEADER_APP = ["site","element","app","latency","jitter","packetloss"]
CSV_HEADER_ALL_APPS = ["site","element","latency","jitter","packetloss"]
CSV_HEADER_MAP = {
    "media": CSV_HEADER_MEDIA,
    "app": CSV_HEADER_APP,
    "all_apps": CSV_HEADER_ALL_APPS
}


try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # will get caught below.
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None

try:
    from cloudgenix_settings import CLOUDGENIX_USER, CLOUDGENIX_PASSWORD

except ImportError:
    # will get caught below
    CLOUDGENIX_USER = None
    CLOUDGENIX_PASSWORD = None

#Global Translation Dictionaries
siteid_sitename_dict = {}
sitename_siteid_dict = {}
siteid_vpnidlist_dict = {}
vpnid_elemid_dict = {}
elemname_elemid_dict = {}
elemid_elemname_dict = {}
elemid_siteid_dict = {}
vpnid_vpnname_dict = {}
appid_appname = {}
appname_appid = {}

def buildtranslationdicts(cgx_session, lqm_type):
    print("INFO: Building translation dicts..")
    print("\tSites")
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        sitelist = resp.cgx_content.get("items",None)

        for site in sitelist:
            sid = site['id']
            sname = site['name']
            if sid == "1":
                continue

            siteid_sitename_dict[sid] = sname
            sitename_siteid_dict[sname] = sid

    print("\tElements")
    resp = cgx_session.get.elements()
    if resp.cgx_status:
        elemlist = resp.cgx_content.get("items", None)

        for elem in elemlist:
            eid = elem['id']
            ename = elem['name']
            sid = elem['site_id']
            if sid == "1":
                continue

            elemname_elemid_dict[ename] = eid
            elemid_elemname_dict[eid] = ename
            elemid_siteid_dict[eid] = sid

    print("\tAppdefs")
    resp = cgx_session.get.appdefs()
    if resp.cgx_status:
        applist = resp.cgx_content.get("items", None)
        for app in applist:
            appid_appname[app["id"]] = app["display_name"]
            appname_appid[app["display_name"]] = app["id"]


    if lqm_type == "media":
        print("\tVPNs")
        for sid in siteid_sitename_dict.keys():
            data = {
                "type":"basenet",
                "site_id":sid,
                "links_only":True
            }

            resp = cgx_session.post.topology(data=data)
            if resp.cgx_status:
                links = resp.cgx_content.get("links",None)
                vpnidlist = []
                for link in links:
                    if link['type'] == "vpn":
                        vpnidlist.append(link['path_id'])
                        vpnid_elemid_dict[link['path_id']] = link['source_node_id']
                        vpnname = "{}:{} - {}:{}".format(link['source_site_name'], link['source_wan_network'], link['target_wan_network'], link['target_site_name'])
                        vpnid_vpnname_dict[link['path_id']] = vpnname

                siteid_vpnidlist_dict[sid] = vpnidlist

    return


def cleanexit(cgx_session):
    print("Logging Out")
    cgx_session.get.logout()
    sys.exit()


def configextention_media(cgx_session, site, latency, jitter, packetloss):

    if site in sitename_siteid_dict.keys():
        sid = sitename_siteid_dict[site]

        if sid in siteid_vpnidlist_dict.keys():
            vpnids = siteid_vpnidlist_dict[sid]

            for vpnid in vpnids:
                name = "{}_lqm".format(vpnid)
                eid = vpnid_elemid_dict[vpnid]

                data = {
                    "name": name,
                    "namespace": "thresholds/lqm/media",
                    "entity_id": vpnid,
                    "disabled": False,
                    "conf": {
                        "max_pkt_loss": packetloss,
                        "max_jitter": jitter,
                        "max_latency": latency
                    }
                }

                resp = cgx_session.post.element_extensions(site_id = sid, element_id = eid, data=data)
                if resp.cgx_status:
                    print("INFO: LQM extensions added to {} {} on path {}:{}".format(site,elemid_elemname_dict[eid],vpnid_vpnname_dict[vpnid],vpnid))

                else:
                    print("ERR: Could not configure LQM threshold on {} {} on path {}:{}".format(site,elemid_elemname_dict[eid],vpnid_vpnname_dict[vpnid],vpnid))
                    cloudgenix.jd_detailed(resp)

        else:
            print("INFO: No VPNs on site {}".format(site))
            return

    else:
        print("ERR: Site {} does not exist".format(site))
        cleanexit(cgx_session)

    return



def configextention_app(cgx_session, site, element, app, latency, jitter, packetloss):

    print(site,element,app)
    if site in sitename_siteid_dict.keys():
        sid = sitename_siteid_dict[site]
        eid = elemname_elemid_dict[element]
        appid = appname_appid[app]
        name = "{}_lqm".format(app)

        latency_en = False
        jitter_en = False
        packetloss_en = False
        if (latency is not None) or (latency != 0):
            latency_en = True

        if (jitter is not None) or (jitter != 0):
            jitter_en = True

        if (packetloss is not None) or (packetloss != 0):
            packetloss_en = True

        data = {
            "name": name,
            "namespace": "thresholds/lqm/app",
            "entity_id": appid,
            "disabled": False,
            "conf": {
                "latency": latency,
                "latency_en": latency_en,
                "jitter": jitter,
                "jitter_en": jitter_en,
                "packet_loss": packetloss,
                "packet_loss_en": packetloss_en
            }
        }

        resp = cgx_session.post.element_extensions(site_id = sid, element_id = eid, data=data)
        if resp.cgx_status:
            print("INFO: LQM thresholds added to {} {} for app {}".format(site,element,app))

        else:
            print("ERR: Could not configure LQM threshold on {} {} for app {}".format(site,element,app))
            cloudgenix.jd_detailed(resp)
    else:
        print("ERR: Site {} does not exist".format(site))
        cleanexit(cgx_session)

    return


def configextention_all_apps(cgx_session, site, element, latency, jitter, packetloss):
    if site in sitename_siteid_dict.keys():
        sid = sitename_siteid_dict[site]
        eid = elemname_elemid_dict[element]

        latency_en = False
        jitter_en = False
        packetloss_en = False
        if (latency is not None) or (latency != 0):
            latency_en = True

        if (jitter is not None) or (jitter != 0):
            jitter_en = True

        if (packetloss is not None) or (packetloss != 0):
            packetloss_en = True

        data = {
            "name": "lqm_all",
            "namespace": "thresholds/lqm/app/all",
            "entity_id": None,
            "disabled": False,
            "conf": {
                "latency": latency,
                "latency_en": latency_en,
                "jitter": jitter,
                "jitter_en": jitter_en,
                "packet_loss": packetloss,
                "packet_loss_en": packetloss_en
            }
        }

        resp = cgx_session.post.element_extensions(site_id=sid, element_id=eid, data=data)
        if resp.cgx_status:
            print("INFO: LQM thresholds added to {} {} for ALL apps".format(site, element))

        else:
            print("ERR: Could not configure LQM threshold on {} {} for ALL apps".format(site, element))
            cloudgenix.jd_detailed(resp)
    else:
        print("ERR: Site {} does not exist".format(site))
        cleanexit(cgx_session)

    return


def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))

    # Allow Controller modification and debug level sets.
    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. "
                                       "C-Prod: https://api.elcapitan.cloudgenix.com",
                                  default="https://api.elcapitan.cloudgenix.com")

    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')
    login_group.add_argument("--email", "-E", help="Use this email as User Name instead of prompting",
                             default=None)
    login_group.add_argument("--pass", "-P", help="Use this Password instead of prompting",
                             default=None)

    # Commandline for entering Site info
    config_group = parser.add_argument_group('LQM Config Specific information',
                                           'Provide value for Latency, Jitter and Packet Loss')
    config_group.add_argument("--sitename", "-SN", help="Name of the Site", default=None)
    config_group.add_argument("--elemname", "-EN", help="Name of the Element", default=None)
    config_group.add_argument("--lqmtype", "-LT", help="Type of LQM config. Allowed values: media, all_apps, app", default=None)
    config_group.add_argument("--appname", "-AN", help="Name of the Element", default=None)
    config_group.add_argument("--latency", "-L", help="Max value for latency", default=0)
    config_group.add_argument("--jitter", "-J", help="Max value for jitter", default=0)
    config_group.add_argument("--packetloss", "-PL", help="Max value for packetloss", default=0)
    config_group.add_argument("--filename", "-f", help="CSV file containing configuration information. CSV header should match: site,element,app,latency,jitter,packetloss", default=None)

    args = vars(parser.parse_args())

    ############################################################################
    # Parse CLI parameters
    ############################################################################
    CONFIGTYPE = None
    lqm_type = args["lqmtype"]
    if lqm_type not in ["media", "all_apps", "app"]:
        print("ERR: Invalid LQM type. Please choose from: media, all_apps, app")
        sys.exit()

    CSV_HEADER = CSV_HEADER_MAP[lqm_type]

    filename = args['filename']
    if filename:
        if not os.path.isfile(filename):
            print("ERR: File {} does not exist. Please enter the accurate file".format(filename))
            sys.exit()
        else:
            CONFIGTYPE = "FILE"
    else:
        site = args['sitename']
        element = args['elemname']
        app = args["appname"]
        latency = packetloss = jitter = 0
        if args['latency'] is not None:
            latency = int(args['latency'])

        if args['jitter'] is not None:
            jitter = int(args['jitter'])

        if args['packetloss'] is not None:
            packetloss = int(args['packetloss'])

        if latency < 0 or jitter<0 or packetloss<0:
            print("ERR: Invalid LQM Threshold values: {} {} {}".format(latency,jitter,packetloss))
            sys.exit()

        CONFIGTYPE = "CLI"

    ############################################################################
    # Instantiate API & Login
    ############################################################################

    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=False)
    print("{0} v{1} ({2})\n".format(SCRIPT_NAME, SDK_VERSION, cgx_session.controller))

    # login logic. Use cmdline if set, use AUTH_TOKEN next, finally user/pass from config file, then prompt.
    # figure out user
    if args["email"]:
        user_email = args["email"]
    elif CLOUDGENIX_USER:
        user_email = CLOUDGENIX_USER
    else:
        user_email = None

    # figure out password
    if args["pass"]:
        user_password = args["pass"]
    elif CLOUDGENIX_PASSWORD:
        user_password = CLOUDGENIX_PASSWORD
    else:
        user_password = None

    # check for token
    if CLOUDGENIX_AUTH_TOKEN and not args["email"] and not args["pass"]:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()

    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None

    ############################################################################
    # Build Translation Dictionaries
    ############################################################################
    buildtranslationdicts(cgx_session, lqm_type)

    ############################################################################
    # Configure SSH Extension
    ############################################################################
    if CONFIGTYPE == "CLI":
        if lqm_type == "media":
            configextention_media(cgx_session=cgx_session, site=site, latency=latency, jitter=jitter, packetloss=packetloss)

        elif lqm_type == "app":
            configextention_app(cgx_session=cgx_session, site=site, element=element, app=app, latency=latency, jitter=jitter, packetloss=packetloss)

        else:
            #lqmtype all_apps
            configextention_all_apps(cgx_session=cgx_session, site=site, element=element, latency=latency, jitter=jitter, packetloss=packetloss)

    else:
        configdata = pd.read_csv(filename)
        columns = list(configdata.columns)

        if set(columns) == set(CSV_HEADER):

            for i,row in configdata.iterrows():
                print("INFO: Configuring row {} from CSV".format(i+1))
                if lqm_type == "media":
                    configextention_media(cgx_session=cgx_session, site=row['site'], latency=row['latency'], jitter=row['jitter'], packetloss=row['packetloss'])

                elif lqm_type == "app":
                    configextention_app(cgx_session=cgx_session, site=row['site'], element=row["element"], app=row["app"],latency=row['latency'], jitter=row['jitter'], packetloss=row['packetloss'])

                else:
                    configextention_all_apps(cgx_session=cgx_session, site=row['site'], element=row["element"], latency=row['latency'], jitter=row['jitter'], packetloss=row['packetloss'])

        else:
            print("ERR: CSV header not in expected format. Please make sure the headers are {}".format(CSV_HEADER))
            cleanexit(cgx_session)


    ############################################################################
    # Logout to clear session.
    ############################################################################
    cleanexit(cgx_session)


if __name__ == "__main__":
    go()