import glob
import json
import ssl
import os
import pprint
import re
import shutil
import subprocess
import urllib.request
from string import Template
from datetime import datetime, timedelta
import time

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36"  # noqa: E501

DAYZ_ROOT="/dayz"
#SHARE_DAYZ_ROOT="/var/run/share/dayz"
COMMON_SHARE_DAYZ_ROOT="/var/run/share/dayz/server-common"
THIS_SHARE_DAYZ_ROOT="/var/run/share/dayz/this-server"
STEAM_ROOT="/steamcmd"

FOLDER_KEYS = DAYZ_ROOT+"/keys"
FOLDER_MODS = DAYZ_ROOT+"/mods"
FOLDER_SERVERMODS = DAYZ_ROOT+"/servermods"
FOLDER_CONFIG = DAYZ_ROOT+"/config"
FOLDER_USERCONFIG = DAYZ_ROOT+"/userconfig"
FOLDER_MPISSIONS = DAYZ_ROOT+"/mpmissions"

CONFIG_FILE = FOLDER_CONFIG+os.sep+os.environ["DAYZ_CONFIG"]

# 1. /dayz/* ordner von "außen" löschen
# 2. /tmp/workshop/.../mods/xxx Ornder von this-server und common-server hierher linken
#                                      fehlende order in common-server anlegen und linken
# 

NEW_MOD_LIST=[]
NEW_SRVMOD_LIST=[]
NEW_MAPS_LIST=[]
WORK_MODS="mods"
WORK_SMODS="servermods"

def logdebug(what, silent=False):
    if not silent:
        print("logdebug  : {}".format(what), flush=True)
def lognotice(what, silent=False):
    if not silent:
        print("NOTICE : {}".format(what), flush=True)
def logwarning(what, silent=False):
    if not silent:
        print("WARNING: {}".format(what), flush=True)
def logerror(what, silent=False):
    if not silent:
        print("ERROR  : {}".format(what), flush=True)

def mod_param(name, mods, subfolder=""):
    m=[]
    for mod in mods:
        m.append(subfolder+mod)
    return ' -{}="{}" '.format(name, ";".join(m))

def check_double_mods(mod_list):
    e=[]
    id=[]
    name=[]
    r=True
    for dispname, steamid in mod_list:
        if not dispname in name and not steamid in id:
            e.append([dispname, steamid])
            id.append(steamid)
            name.append(dispname)
        elif not steamid in id and dispname in name:
            logerror("modname {} is used multiple times".format(dispname))
            r=False
        else:
            logerror("steamid {} is used multiple times".format(steamid))
            r=False
    return r,e

def env_defined(key):
    return key in os.environ and len(os.environ[key]) > 0

def make_sure_dir(path, silent=False):
    if not os.path.isdir(path):
        if os.path.exists(path):
            logwarning("{} is not a dir, removing".format(path))
            os.remove(path)
        os.makedirs(path)
        lognotice("{} created".format(path), silent)
    else:
        logerror("{} is a file and not a path".format(path))

def link_it(what, to, silent=False):
    if not os.path.exists(to):
        try:
            os.symlink(what, to)
            lognotice("{} linked to {}".format(what, to), silent=silent)
        except:
            logerror("{} failed to link to {}".format(what, to))
    else:
        logwarning("{} exists, cannot link {}".format(to, what))

def copy_key(moddir, keyfolder, steamid, dispname=""):
    keys = glob.glob(os.path.join(moddir, "**/*.bikey"))
    if len(keys) > 0:
        for key in keys:
            if not os.path.isdir(key):
                shutil.copy2(key, keyfolder+os.sep+steamid+"_"+os.path.basename(key))
    else:
        logwarning("Missing keys: {} ({})".format(moddir, dispname))
        
def fix_folder_characters(path):
    for subdir, dirs, files in os.walk(path):
        for file in files:
            if file.lower()!=file and (file.endswith(".pbo") or file.endswith(".paa") or file.endswith(".sqf")):
                #lognotice("to lower FILE: {} -> {}".format(subdir + os.sep + file, file.lower()))
                #os.rename(subdir + os.sep + file, subdir + os.sep + file.lower())

                for sfile in files:
                    if sfile.startswith(file) and sfile.lower() != sfile:
                        lognotice("to lower FILE: {} -> {}".format(subdir + os.sep + sfile, sfile.lower()))
                        os.rename(subdir + os.sep + sfile, subdir + os.sep + sfile.lower())
                        
        for dir in dirs:
            if dir!=dir.lower():
                lognotice("to lower DIR: {} -> {}".format(subdir + os.sep + dir, subdir + os.sep + dir.lower()))
                os.rename(subdir + os.sep + dir, subdir + os.sep + dir.lower())
            fix_folder_characters(subdir + os.sep + dir.lower())

def get_last_update(steamid):
    dt_1=datetime.now()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url_string="https://steamcommunity.com/sharedfiles/filedetails/"+str(steamid)
    dt_2=datetime.now()
    req = urllib.request.Request(url_string, headers={"User-Agent": USER_AGENT})
    remote = urllib.request.urlopen(req)
    html=remote.read().decode(remote.headers.get_content_charset());
    #html=html.split("detailsStatsContainerRight",1)[1].split("detailsStatsContainerRight",1)[0]
    dt_3=datetime.now()
    
    regex=r"\"detailsStatRight\".*>(.*)<.*\/div.*>"
    matches=re.findall(regex, html, re.MULTILINE)

    dt=datetime.now().replace(year=1984)
    dt_4=datetime.now()
    if len(matches)==2:
        
        try:
            dt=datetime.strptime(matches[1], "%d %b, %Y @ %I:%M%p")
        except ValueError:
            dt=datetime.strptime(matches[1], "%d %b @ %I:%M%p")
            dt=dt.replace(year=datetime.now().year)
        #lognotice("mod release time: {}".format(dt))
        #dt_5=datetime.now()
        #lognotice("time: {},{},{},{}".format(dt_2-dt_1, dt_3-dt_2, dt_4-dt_3, dt_5-dt_4 ))
        return dt
    elif len(matches)==3:    
        try:
            dt=datetime.strptime(matches[2], "%d %b, %Y @ %I:%M%p")
        except ValueError:
            dt=datetime.strptime(matches[2], "%d %b @ %I:%M%p")
            dt=dt.replace(year=datetime.now().year)
        #lognotice("mod update time: {}".format(dt))
        #dt_5=datetime.now()
        #lognotice("time: {},{},{},{}".format(dt_2-dt_1, dt_3-dt_2, dt_4-dt_3, dt_5-dt_4 ))
        return dt
        
    logerror("failed to find any release or update date, using fallback-default of {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
    return dt          

def startup_folder_clean_prepare():
    to_unlink=[]
    to_rmtree=[]
    to_ignore=[]

    for item in os.listdir(DAYZ_ROOT):
        if item == "steamapps" or item == "battleye" or item == "dta" or item == "addons":
            continue
        if os.path.islink(item):
            to_unlink.append(item)
        elif os.path.isdir(item):
            to_rmtree.append(item)
        else:
            to_ignore.append(item)

    logdebug("unlinking {}".format(to_unlink))
    for item in to_unlink:
        os.unlink(item)
    logdebug("removing {}".format(to_rmtree))
    for item in to_rmtree:
        shutil.rmtree(item)

    logwarning("ignoring {}".format(to_ignore))

    to_make=[]
    to_link=[]
    to_make.append(FOLDER_KEYS)
    to_make.append(FOLDER_MODS)
    to_make.append(FOLDER_SERVERMODS)
    #to_make.append(FOLDER_MPISSIONS)


    to_link.append([THIS_SHARE_DAYZ_ROOT+"/config", DAYZ_ROOT+"/config"])
    #to_link.append([THIS_SHARE_DAYZ_ROOT+"/userconfig", DAYZ_ROOT+"/userconfig"])
    to_link.append([THIS_SHARE_DAYZ_ROOT+"/logs", DAYZ_ROOT+"/logs"])
    to_link.append([THIS_SHARE_DAYZ_ROOT+"/mpmissions", FOLDER_MPISSIONS])
    
    logdebug("creating {}".format(to_make))
    for item in to_make:
        make_sure_dir(item, silent=True)
    logdebug("linking {}".format(to_link))
    for item_from, item_to in to_link:
        link_it(item_from, item_to, silent=True)

def detect_mods():
    mods=[]
    smods=[]

    src_folder=THIS_SHARE_DAYZ_ROOT+"/mods/"
    dirs=os.listdir(src_folder)
    for dir in dirs:
        if dir.startswith("@"):
            fix_folder_characters(src_folder+dir)
            link_it(src_folder+dir, FOLDER_MODS+os.sep+dir)
            copy_key(FOLDER_MODS+os.sep+dir, FOLDER_KEYS, dir)
            mods.append(dir)
    
    src_folder=THIS_SHARE_DAYZ_ROOT+"/servermods/"
    dirs=os.listdir(src_folder)
    for dir in dirs:
        if dir.startswith("@"):
            fix_folder_characters(src_folder+dir)
            link_it(src_folder+dir, FOLDER_SERVERMODS+os.sep+dir)
            copy_key(FOLDER_SERVERMODS+os.sep+dir, FOLDER_KEYS, dir)
            smods.append(dir)
    
    return mods, smods

print("\n\nHALLO WELT, HALLO DON!\n", flush=True)
debug_skip_install=False
#while(True):
#    time.sleep(1)
lognotice("\npreparing server...")

# remove folder and links and prepare new ones
startup_folder_clean_prepare()
server_mods=[]
mods=[]

mods,server_mods=detect_mods()

# add the server itself
lognotice("\ninstall / update arma server binary...")
    
if os.environ["SKIP_INSTALL"] in ["", "false"] and debug_skip_install==False:
    # Install Arma

    steamcmd = ["/steamcmd/steamcmd.sh"]
    steamcmd.extend(["+force_install_dir", "/dayz"])
    steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
    steamcmd.extend(["+app_update", "223350"])
    steamcmd.extend(["validate"])
    steamcmd.extend(["+quit"])
    subprocess.call(steamcmd)

# Mods

launch = "{} -filePatching -limitFPS={} {} ".format(
    os.environ["DAYZ_BINARY"],
    os.environ["DAYZ_LIMITFPS"],
    os.environ["DAYZ_PARAMS"]
)

if len(mods):
    launch += mod_param("mod", mods, "mods/")

launch += ' -config="{}"'.format(CONFIG_FILE)

#lognotice("sleeping!")
#while(True):
#    time.sleep(1)
    
lognotice("\nstarting dayz dedicated server...")


launch += ' -port={} -name="{}" -dologs -adminlog -netlog -profiles="/dayz/config/profiles"'.format(
    os.environ["PORT"], os.environ["DAYZ_PROFILE"]
)

if len(server_mods):
    launch += mod_param("serverMod", server_mods, "servermods/")

print("LAUNCHING DAYZ SERVER WITH", launch, flush=True)

os.system(launch)
