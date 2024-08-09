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

ARMA_ROOT="/arma3"
SHARE_ARMA_ROOT="/var/run/share/arma3"
COMMON_SHARE_ARMA_ROOT="/var/run/share/arma3/server-common"
THIS_SHARE_ARMA_ROOT="/var/run/share/arma3/this-server"
STEAM_ROOT="/steamcmd"

FOLDER_KEYS = ARMA_ROOT+"/keys"
FOLDER_MODS = ARMA_ROOT+"/mods"
FOLDER_SERVERMODS = ARMA_ROOT+"/servermods"
FOLDER_ADDONS = ARMA_ROOT+"/addons"
FOLDER_CONFIG = ARMA_ROOT+"/config"
FOLDER_USERCONFIG = ARMA_ROOT+"/userconfig"
FOLDER_MPISSIONS = ARMA_ROOT+"/mpmissions"

CONFIG_FILE = FOLDER_CONFIG+os.sep+os.environ["ARMA_CONFIG"]
SERVER_BASE = ARMA_ROOT+os.sep+os.environ["BASIC_CONFIG"]
PARAM_FILE = FOLDER_CONFIG+os.sep+os.environ["PARAM_CONFIG"]
PRESET_FILE=FOLDER_CONFIG+os.sep+os.environ["MODS_PRESET"]
JSON_CONFIG = FOLDER_CONFIG+os.sep+"server.json"
WORKSHOP_DIR="/tmp"+os.sep+"steamapps/workshop/content/107410"+os.sep

NEW_MOD_LIST=None
NEW_SRVMOD_LIST=None
WORK_MODS="mods"
WORK_SMODS="servermods"

def logdebug(what):
    print("logdebug  : {}".format(what), flush=True)
def lognotice(what):
    print("NOTICE : {}".format(what), flush=True)
def logwarning(what):
    print("WARNING: {}".format(what), flush=True)
def logerror(what):
    print("ERROR  : {}".format(what), flush=True)

def mod_param(name, mods):
    return ' -{}="{}" '.format(name, ";".join(mods))


def env_defined(key):
    return key in os.environ and len(os.environ[key]) > 0

def make_sure_dir(path):
    if not os.path.isdir(path):
        if os.path.exists(path):
            logwarning("{} is not a dir, removing".format(path))
            os.remove(path)
        os.makedirs(path)
        lognotice("{} created".format(path))
    else:
        logerror("{} is a file and not a path".format(path))

def link_it(what, to, keep_silent=False):
    if not os.path.exists(to):
        try:
            os.symlink(what, to)
            lognotice("{} linked to {}".format(what, to))
        except:
            logerror("{} failed to link to {}".format(what, to))
    else:
        if not keep_silent:
            logwarning("{} exists, cannot link {}".format(to, what))

def get_folder_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
    
def get_mods_from_dir(d, type="mods"):
    mods = []

    # Find mod folders
    for m in os.listdir(d):
        moddir = os.path.join(d, m)
        moddir=type+"/"+m
        #logdebug("mods: {}".format(moddir))
        mods.append(moddir)

    return mods

def copy_key(moddir, keyfolder):
    keys = glob.glob(os.path.join(moddir, "**/*.bikey"))
    if len(keys) > 0:
        for key in keys:
            if not os.path.isdir(key):
                shutil.copy2(key, keyfolder)
    else:
        logwarning("Missing keys: {}".format(moddir))
        
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
        lognotice("mod release time: {}".format(dt))
        dt_5=datetime.now()
        lognotice("time: {},{},{},{}".format(dt_2-dt_1, dt_3-dt_2, dt_4-dt_3, dt_5-dt_4 ))
        return dt
    elif len(matches)==3:    
        try:
            dt=datetime.strptime(matches[2], "%d %b, %Y @ %I:%M%p")
        except ValueError:
            dt=datetime.strptime(matches[2], "%d %b @ %I:%M%p")
            dt=dt.replace(year=datetime.now().year)
        lognotice("mod update time: {}".format(dt))
        dt_5=datetime.now()
        lognotice("time: {},{},{},{}".format(dt_2-dt_1, dt_3-dt_2, dt_4-dt_3, dt_5-dt_4 ))
        return dt
        
    logerror("failed to find any release or update date, using fallback-default of {}".format(dt.strftime("%Y-%m-%d %H:%M:%S")))
    return dt

        
def steam_download(mods, type="mods", validate=False):
    if len(mods) == 0:
        return
    share_dir=""
    if type=="mods":
        share_dir=COMMON_SHARE_ARMA_ROOT+os.sep+"mods"+os.sep
    elif type=="servermods":
        share_dir=THIS_SHARE_ARMA_ROOT+os.sep+"servermods"+os.sep
    else:
        logerror("whoops type={}".format(type))
    
        
    for dispname, steamid in mods:
        run_steamcmd=False
        up_dt=datetime.now().replace(year=1984)
        datecfg=share_dir+steamid+os.sep+"srvdon_info.cfg"
        if os.path.exists(share_dir+steamid):
            if not os.path.exists(datecfg):
                with open(datecfg, "w") as f:
                    dt=datetime.now().replace(year=1984)
                    f.write(dt.strftime("%Y-%m-%d %H:%M:%S"))
                    logwarning("failed to find last update time, setting default for {} to {}".format(datecfg, dt.strftime("%Y-%m-%d %H:%M:%S")) )
            if validate:
                act_dt=datetime.now().replace(year=1984)
                try:
                    with open(datecfg, "r") as f:
                        act_dt=datetime.strptime(f.read(), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logerror("failed to get update time from {}".format(datecfg))
                    os.remove(datecfg)
                    act_dt=datetime.now().replace(year=1984)
                up_dt=get_last_update(steamid)
                if up_dt is None:
                    logwarning("mod {} ({}) not found".format(dispname, steamid))
                elif up_dt > act_dt:
                    run_steamcmd=True
                else:
                    lognotice("mod {} ({}) seems to be up to date".format(dispname, steamid))
        else:
            make_sure_dir(share_dir+steamid)
            run_steamcmd=True
            logwarning("getting release date of mod {} ({})".format(dispname, steamid))
            up_dt=get_last_update(steamid)
            link_it(share_dir+steamid, WORKSHOP_DIR+steamid)
        
        if run_steamcmd:
            steamcmd = ["/steamcmd/steamcmd.sh"]
            steamcmd.extend(["+force_install_dir", "/tmp"])
            steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
            steamcmd.extend(["+workshop_download_item", "107410", steamid, "validate"])
            steamcmd.extend(["+quit"])
            lognotice("mod downloading: {} ({}): {}".format(dispname, steamid, steamcmd));
            subprocess.call(steamcmd)
            with open(datecfg, "w") as f:
                f.write(up_dt.strftime("%Y-%m-%d %H:%M:%S"))
                lognotice("updated mod update time of {} to {}".format(datecfg, up_dt.strftime("%Y-%m-%d %H:%M:%S")) )
            
        if type=="mods":
            link_it(share_dir, FOLDER_MODS+os.sep+steamid, keep_silent=True)
            copy_key(FOLDER_MODS+os.sep+steamid, FOLDER_KEYS)
        elif type=="servermods":
            link_it(share_dir, FOLDER_SERVERMODS+os.sep+steamid, keep_silent=True)
            copy_key(FOLDER_SERVERMODS+os.sep+steamid, FOLDER_KEYS)
            



def filter_preset_mods(local_mods, preset_file=None, cfg_list=None, type="mods"):
    mods = []
    mis = []
    check = []
    presmods=[]
    moddirs = []
    if not preset_file is None:
        with open(preset_file) as f:
            html = f.read()
            lognotice("modfolder - config size {}".format(len(html)))
            regex=r"<tr[\s\S]*?DisplayName\">(.*?)<\/td>[\s\S]*?filedetails\/\?id=(\d+)[\s\S]*?<\/tr>"
    
            matches = re.finditer(regex, html, re.MULTILINE)
            
            cfg_list=[]
            for _, match in enumerate(matches, start=1):
                dispname=match.group(1).replace(":","-").rstrip(".,")
                cfg_list.append([dispname, match.group(2)])
            pprint.pp(cfg_list)   
                
    if not cfg_list is None:
        i=0
        for moditem in cfg_list:
            dispname = moditem[0]
            steamid = moditem[1]
                
            if type+"/@" + dispname in local_mods: 
                moddir = type+"/@" + dispname
                s=get_folder_size(ARMA_ROOT+os.sep+moddir)
                moddirs.append(moddir)
                if not steamid is None:
                    check.append(moditem)
                lognotice("modfolder {} found : {} ({})".format(i, moddir, float(s)/1048576))
            elif not steamid is None and "mods/" + steamid in local_mods: 
                moddir = type+"/" + steamid
                moddirs.append(moddir)
                lognotice("modfolder {} found: {} for {}".format(i, moddir, dispname))
                check.append(moditem)
            elif not steamid is None:
                logwarning("modfolder {} not found: @{} or {}".format(i, dispname, steamid))
                moddir = type+"/" + steamid
                moddirs.append(moddir)
                mis.append(moditem)
            i+=1
            
        if len(mis) > 0:
            lognotice("downloading mods: {}".format(mis))
            steam_download(mis, type=type)
        if len(check) > 0:
            lognotice("check for update of mods: {} ({})".format(check, len(check)))
            steam_download(check, type=type, validate=True)
        moddirs=[]
        for dispname,steamid in cfg_list:
            link_it(steamid, type+"/@" + dispname)
            moddirs.append( type+"/@" + dispname)
    return moddirs

def correct_server_mods(smods):
    mods = []
    WORK_SMODS
    for mod in smods:
        modname=os.path.basename(os.path.normpath(mod))
        mods.append(mods)
    return mods


print("\n\nHALLO WELT, HALLO DON!\n", flush=True)
debug_skip_install=False

    
lognotice("\npreparing server...")

for item in os.listdir(ARMA_ROOT):
    if item == "steamapps" or item == "battleye":
        continue
    if os.path.islink(item):
        logdebug("unlink {}".format(item))
        os.unlink(item)
    elif os.path.isdir(item):
        logdebug("rm {}".format(item))
        shutil.rmtree(item)
    else:
        logwarning("unknown {}".format(item))
if os.path.exists(WORKSHOP_DIR):
    logdebug("rm {}".format(WORKSHOP_DIR))
    shutil.rmtree(WORKSHOP_DIR)
# prepare folders from outside and inside

make_sure_dir(FOLDER_KEYS)
make_sure_dir(FOLDER_MODS)
make_sure_dir(FOLDER_SERVERMODS)
make_sure_dir(WORKSHOP_DIR)
#make_sure_dir(FOLDER_ADDONS)
#make_sure_dir(FOLDER_MPISSIONS)
 
link_it(THIS_SHARE_ARMA_ROOT+"/config", ARMA_ROOT+"/config")
link_it(THIS_SHARE_ARMA_ROOT+"/userconfig", ARMA_ROOT+"/userconfig")
link_it(THIS_SHARE_ARMA_ROOT+"/logs", ARMA_ROOT+"/logs")

if os.path.exists(THIS_SHARE_ARMA_ROOT+"/mpmissions"):
    link_it(THIS_SHARE_ARMA_ROOT+"/mpmissions", ARMA_ROOT+"/mpmissions")

#if os.path.exists(THIS_SHARE_ARMA_ROOT+"/maps"):
#    link_it(THIS_SHARE_ARMA_ROOT+"/maps", ARMA_ROOT+"/maps")

#if os.path.exists(COMMON_SHARE_ARMA_ROOT+"/maps"):
#    for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/maps"):
#        src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/maps", item)
#        fix_folder_characters(src)
#        link_it(src, FOLDER_MODS+os.sep+item)
#        copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)

    
lognotice("1 - processing THIS_SHARE_ARMA_ROOT/servermods: {}".format(THIS_SHARE_ARMA_ROOT+"/servermods"))     
for item in os.listdir(THIS_SHARE_ARMA_ROOT+"/servermods"):
    src=os.path.join(THIS_SHARE_ARMA_ROOT+"/servermods", item)
    fix_folder_characters(src)
    link_it(src, FOLDER_SERVERMODS+os.sep+item)
    copy_key(FOLDER_SERVERMODS+os.sep+item, FOLDER_KEYS)

lognotice("2 - processing THIS_SHARE_ARMA_ROOT/mods: {}".format(THIS_SHARE_ARMA_ROOT+"/mods"))         
for item in os.listdir(THIS_SHARE_ARMA_ROOT+"/mods"):
    src=os.path.join(THIS_SHARE_ARMA_ROOT+"/mods", item)
    fix_folder_characters(src)
    link_it(src, FOLDER_MODS+os.sep+item)
    copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)
    
lognotice("3 - processing COMMON_SHARE_ARMA_ROOT/mods: {}".format(COMMON_SHARE_ARMA_ROOT+"/mods"))    
for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/mods"):
    src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/mods", item)
    fix_folder_characters(src)
    link_it(src, FOLDER_MODS+os.sep+item)
    copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)

lognotice("4 - processing COMMON_SHARE_ARMA_ROOT/dlcs: {}".format(COMMON_SHARE_ARMA_ROOT+"/dlcs")) 
for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/dlcs"):
    src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/dlcs", item)
    fix_folder_characters(src)
    link_it(src, ARMA_ROOT+os.sep+item)
    copy_key(ARMA_ROOT+os.sep+item, FOLDER_KEYS)

lognotice("\nchecking for json config...")

jconfig=None
if os.path.exists(JSON_CONFIG):
    lognotice("found server.json override file")
    with open(JSON_CONFIG) as f:
        try:
            jconfig = json.load(f)
        except:
            logerror("failed to load {}".format(JSON_CONFIG))

if not jconfig is None:
    active_jcname=jconfig.get("config-name", None);
    debug_skip_install=jconfig.get("debug_skip_install", False)
    if not active_jcname is None:
        lognotice("config {} is selected in json file".format(active_jcname))
        active_jc=jconfig.get("configs",{}).get(active_jcname, None)
        if not active_jc is None:
            if "server-config-file" in active_jc:
                lognotice("overwrite ARMA_CONFIG with {}".format(active_jc["server-config-file"]))
                os.environ["ARMA_CONFIG"] = active_jc["server-config-file"]
                CONFIG_FILE = FOLDER_CONFIG+os.sep+os.environ["ARMA_CONFIG"]
            if "server-parameters" in active_jc:
                lognotice("overwrite ARMA_PARAMS with {}".format(active_jc["server-parameters"]))
                os.environ["ARMA_PARAMS"] = active_jc["server-parameters"]
                PARAM_FILE = "/does-not-exist"
            if "server-base-file" in active_jc:
                lognotice("overwrite BASIC_CONFIG with {}".format(active_jc["server-base-file"]))
                os.environ["BASIC_CONFIG"] = active_jc["server-base-file"]
                SERVER_BASE = FOLDER_CONFIG+os.sep+os.environ["BASIC_CONFIG"]
            if "servermods" in active_jc:
                NEW_SRVMOD_LIST=active_jc["servermods"]
                logwarning("validating servermods: {}".format(NEW_SRVMOD_LIST))
            if "mods" in active_jc:
                NEW_MOD_LIST=active_jc["mods"]
                logwarning("validating mods: {}".format(NEW_MOD_LIST))
            elif "mod-config-file" in active_jc:
                lognotice("overwrite MODS_PRESET with {}".format(active_jc["mod-config-file"]))
                os.environ["MODS_PRESET"] = active_jc["mod-config-file"]
                PRESET_FILE = FOLDER_CONFIG+os.sep+os.environ["MODS_PRESET"]
            if "num-headless" in active_jc:
                lognotice("overwrite HEADLESS_CLIENTS with {}".format(active_jc["num-headless"]))
                os.environ["HEADLESS_CLIENTS"]=str(active_jc["num-headless"])
            if not active_jc.get("creator-dlc", None) is None:
                if active_jc["creator-dlc"].get("enable-creator", False):
                    os.environ["STEAM_BRANCH"]="creatordlc"
                    os.environ["STEAM_BRANCH_PASSWORD"]=""
                    os.environ["ARMA_CDLC"]=""
                if active_jc["creator-dlc"].get("csla-iron-curtain", False):
                    if len(os.environ["ARMA_CDLC"]) > 0:
                        os.environ["ARMA_CDLC"]+=";"
                    os.environ["ARMA_CDLC"]+="csla"
                if active_jc["creator-dlc"].get("global-mobilization-cold-war", False):
                    if len(os.environ["ARMA_CDLC"]) > 0:
                        os.environ["ARMA_CDLC"]+=";"
                    os.environ["ARMA_CDLC"]+="gm"
                if active_jc["creator-dlc"].get("s.o.g.-prairie-fire", False):
                    if len(os.environ["ARMA_CDLC"]) > 0:
                        os.environ["ARMA_CDLC"]+=";"
                    os.environ["ARMA_CDLC"]+="vn"
                if active_jc["creator-dlc"].get("western-sahara", False):
                    if len(os.environ["ARMA_CDLC"]) > 0:
                        os.environ["ARMA_CDLC"]+=";"
                    os.environ["ARMA_CDLC"]+="ws"
                if active_jc["creator-dlc"].get("spearhead-1944", False):
                    if len(os.environ["ARMA_CDLC"]) > 0:
                        os.environ["ARMA_CDLC"]+=";"
                    os.environ["ARMA_CDLC"]+="spe"
        else:
            logerror("no config entry with key {} found in json file".format(active_jcname))
                        


link_it(COMMON_SHARE_ARMA_ROOT+"/basic.cfg", ARMA_ROOT+"/basic.cfg")

# add the server itself


lognotice("\ninstall / update arma server binary...")
    
if os.environ["SKIP_INSTALL"] in ["", "false"] and debug_skip_install==False:
    # Install Arma

    steamcmd = ["/steamcmd/steamcmd.sh"]
    steamcmd.extend(["+force_install_dir", "/arma3"])
    steamcmd.extend(["+login", os.environ["STEAM_USER"], os.environ["STEAM_PASSWORD"]])
    steamcmd.extend(["+app_update", "233780"])
    if env_defined("STEAM_BRANCH"):
        steamcmd.extend(["-beta", os.environ["STEAM_BRANCH"]])
    if env_defined("STEAM_BRANCH_PASSWORD"):
        steamcmd.extend(["-betapassword", os.environ["STEAM_BRANCH_PASSWORD"]])
    steamcmd.extend(["validate"])
    steamcmd.extend(["+quit"])
    subprocess.call(steamcmd)

# Mods


lognotice("\nchecking mods...")


mods = []
local_mods = []     # all possible mods
preset_mods = []
server_mods=[]

if os.path.exists(ARMA_ROOT+os.sep+"mods"):
    local_mods.extend(get_mods_from_dir(FOLDER_MODS))

if not NEW_MOD_LIST is None:
    preset_mods.extend(filter_preset_mods(local_mods, cfg_list=NEW_MOD_LIST))
    mods.extend(preset_mods)
elif os.environ["MODS_PRESET"] != "":
    preset_mods.extend(filter_preset_mods(local_mods, preset_file=PRESET_FILE))
    mods.extend(preset_mods)

mods_size=0
for mod in mods:
    mods_size+=get_folder_size(ARMA_ROOT+os.sep+mod)

lognotice("estimated size of mods: {}".format(mods_size))

server_mods=get_mods_from_dir(FOLDER_SERVERMODS, type="servermods")
if not NEW_SRVMOD_LIST is None:
    lognotice("{} --- {}".format(server_mods,NEW_SRVMOD_LIST))
    server_mods=filter_preset_mods(server_mods, cfg_list=NEW_SRVMOD_LIST, type="servermods")

launch = "{} -filePatching -limitFPS={} -world={} {} {}".format(
    os.environ["ARMA_BINARY"],
    os.environ["ARMA_LIMITFPS"],
    os.environ["ARMA_WORLD"],
    os.environ["ARMA_PARAMS"],
    mod_param("mod", mods)
)

if os.environ["ARMA_CDLC"] != "":
    for cdlc in os.environ["ARMA_CDLC"].split(";"):
        launch += " -mod={}".format(cdlc)



clients = int(os.environ["HEADLESS_CLIENTS"])
if clients > 0:
    lognotice("\nstarting {} headless clients...".format(clients))

if clients != 0:
    with open(CONFIG_FILE) as config:
        data = config.read()
        regex = r"(.+?)(?:\s+)?=(?:\s+)?(.+?)(?:$|\/|;)"

        config_values = {}

        matches = re.finditer(regex, data, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            config_values[match.group(1).lower()] = match.group(2)

        if "headlessclients[]" not in config_values:
            data += '\nheadlessclients[] = {"127.0.0.1"};\n'
        if "localclient[]" not in config_values:
            data += '\nlocalclient[] = {"127.0.0.1"};\n'

        with open("/tmp/arma3.cfg", "w") as tmp_config:
            tmp_config.write(data)
        launch += ' -config="/tmp/arma3.cfg"'

    client_launch = launch
    client_launch += " -client -connect=127.0.0.1 -port={}".format(os.environ["PORT"])
    if "password" in config_values:
        client_launch += " -password={}".format(config_values["password"])

    for i in range(0, clients):
        hc_template = Template(
            os.environ["HEADLESS_CLIENTS_PROFILE"]
        )  # eg. '$profile-hc-$i'
        hc_name = hc_template.substitute(
            profile=os.environ["ARMA_PROFILE"], i=i, ii=i + 1
        )

        hc_launch = client_launch + ' -name="{}"'.format(hc_name)
        print("LAUNCHING ARMA CLIENT {} WITH".format(i), hc_launch)
        subprocess.Popen(hc_launch, shell=True)

else:
    launch += ' -config="{}"'.format(CONFIG_FILE)

#lognotice("sleeping!")
#while(True):
#    time.sleep(1)
    
lognotice("\nstarting arma dedicated server...")


launch += ' -port={} -name="{}" -profiles="/arma3/config/profiles"'.format(
    os.environ["PORT"], os.environ["ARMA_PROFILE"]
)
if os.path.exists(SERVER_BASE):
    launch += ' -cfg="{}"'.format(SERVER_BASE)
if os.path.exists(PARAM_FILE):
    with open(PARAM_FILE) as f:
        cfg_param=f.readline()
        launch += ' {} '.format(cfg_param)

if len(server_mods):
    launch += mod_param("serverMod", server_mods)

print("LAUNCHING ARMA SERVER WITH", launch, flush=True)

os.system(launch)
