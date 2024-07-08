import glob
import os
import re
import shutil
import subprocess
from string import Template
import time

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

def link_it(what, to):
    if not os.path.exists(to):
        os.symlink(what, to)
        lognotice("{} linked to {}".format(what, to))
    else:
        logwarning("{} exists, cannot link {}".format(to, what))

def get_mods_from_dir(d):
    mods = []

    # Find mod folders
    for m in os.listdir(d):
        moddir = os.path.join(d, m)
        moddir="mods/"+m
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

    
def filter_preset_mods(preset_file, local_mods):
    mods = []
    presmods=[]
    moddirs = []
    with open(preset_file) as f:
        html = f.read()
        regex=r"<tr[\s\S]*?DisplayName\">(.*?)<\/td>[\s\S]*?filedetails\/\?id=(\d+)[\s\S]*?<\/tr>"

        matches = re.finditer(regex, html, re.MULTILINE)
        for _, match in enumerate(matches, start=1):
            dispname=match.group(1).replace(":","-")
            #for mod in local_mods:
                #logdebug("mod: {} - {}".format(mod, dispname))
            #    if os.path.basename(os.path.normpath(mod))=="@"+dispname:
            #        moddirs.append(mod)
            if "mods/@" + dispname in local_mods: 
                moddir = "mods/@" + dispname
                moddirs.append(moddir)
            
    return moddirs

def correct_server_mods(smods):
    mods = []
    WORK_SMODS
    for mod in smods:
        modname=os.path.basename(os.path.normpath(mod))
        mods.append(mods)
    return mods

print("", flush=True)
print("", flush=True)
print("HALLO WELT, HALLO DON!", flush=True)

lognotice("preparing server...")
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

# prepare folders from outside and inside

make_sure_dir(FOLDER_KEYS)
make_sure_dir(FOLDER_MODS)
make_sure_dir(FOLDER_SERVERMODS)
make_sure_dir(FOLDER_ADDONS)
#make_sure_dir(FOLDER_MPISSIONS)
 
link_it(THIS_SHARE_ARMA_ROOT+"/config", ARMA_ROOT+"/config")
link_it(THIS_SHARE_ARMA_ROOT+"/userconfig", ARMA_ROOT+"/userconfig")
link_it(THIS_SHARE_ARMA_ROOT+"/logs", ARMA_ROOT+"/logs")

if os.path.exists(THIS_SHARE_ARMA_ROOT+"/mpmissions"):
    link_it(THIS_SHARE_ARMA_ROOT+"/mpmissions", ARMA_ROOT+"/mpmissions")

if os.path.exists(THIS_SHARE_ARMA_ROOT+"/maps"):
    link_it(THIS_SHARE_ARMA_ROOT+"/maps", ARMA_ROOT+"/mods")

if os.path.exists(COMMON_SHARE_ARMA_ROOT+"/maps"):
    for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/maps"):
        src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/maps", item)
        link_it(src, FOLDER_MODS+os.sep+item)
        copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)
        
for item in os.listdir(THIS_SHARE_ARMA_ROOT+"/mods"):
    src=os.path.join(THIS_SHARE_ARMA_ROOT+"/mods", item)
    link_it(src, FOLDER_MODS+os.sep+item)
    copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)

for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/mods"):
    src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/mods", item)
    link_it(src, FOLDER_MODS+os.sep+item)
    copy_key(FOLDER_MODS+os.sep+item, FOLDER_KEYS)
    
for item in os.listdir(COMMON_SHARE_ARMA_ROOT+"/dlcs"):
    src=os.path.join(COMMON_SHARE_ARMA_ROOT+"/dlcs", item)
    link_it(src, ARMA_ROOT+os.sep+item)
    copy_key(ARMA_ROOT+os.sep+item, FOLDER_KEYS)
    
for item in os.listdir(THIS_SHARE_ARMA_ROOT+"/servermods"):
    src=os.path.join(THIS_SHARE_ARMA_ROOT+"/servermods", item)
    link_it(src, FOLDER_SERVERMODS+os.sep+item)
    copy_key(FOLDER_SERVERMODS+os.sep+item, FOLDER_KEYS)

link_it(COMMON_SHARE_ARMA_ROOT+"/basic.cfg", ARMA_ROOT+"/basic.cfg")

# add the server itself

if os.environ["SKIP_INSTALL"] in ["", "false"]:
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

mods = []
local_mods = []     # all possible mods
preset_mods = []
server_mods=[]

if os.path.exists(ARMA_ROOT+os.sep+"mods"):
    local_mods.extend(get_mods_from_dir(FOLDER_MODS))

if os.environ["MODS_PRESET"] != "":
    preset_mods.extend(filter_preset_mods(PRESET_FILE, local_mods))
    mods.extend(preset_mods)

server_mods=get_mods_from_dir(FOLDER_SERVERMODS)

launch = "{} -filePatching -limitFPS={} -world={} {} {}".format(
    os.environ["ARMA_BINARY"],
    os.environ["ARMA_LIMITFPS"],
    os.environ["ARMA_WORLD"],
    os.environ["ARMA_PARAMS"],
    mod_param("mod", mods),
)

if os.environ["ARMA_CDLC"] != "":
    for cdlc in os.environ["ARMA_CDLC"].split(";"):
        launch += " -mod={}".format(cdlc)
print("WOULD LAUNCH ARMA SERVER WITH", launch, flush=True)
clients = int(os.environ["HEADLESS_CLIENTS"])
print("Headless Clients:", clients)

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
