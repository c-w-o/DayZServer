# DayZ Dedicated Server

An DayZ Dedicated Server. Updates to the latest version every time it is restarted. Ripoff of [Arma 3 Dedicated Server](https://github.com/c-w-o/Arma3Server), but much simpler. I do not like to buy DayZ for my server instance and I do not want to use my private steam account for the server. Therefore, we cannot access the workshop of DayZ with steamcmd. 

## Expected / preferred folder structure on host

```
/home/docker/dayz
    + server-0
         + config
         |    + serverDZ.cfg
         |    + profiles
         + logs
         + mods
         |    + < server instance specific mods >
         + mpmissions
         |    + dayzOffline.chernarusplus
         + servermods
              + @FileXT


```


## Usage



### docker-compose

Use the docker-compose.yml file inside a folder. It will automatically create 4 folders in which the missions, configs, mods and servermods can be loaded.

Copy the `.env.example` file to `.env`, containing at least `STEAM_USER` and `STEAM_PASSWORD`.

Use `docker-compose start` to start the server.

Use `docker-compose logs` to see server logs.

Use `docker-compose down` to shutdown the server.

The `network_mode: host` can be changed to explicit ports if needed.

Use `docker-compose up -d` to start the server, detached.

See [Docker-compose](https://docs.docker.com/compose/install/#install-compose) for an installation guide.

Profiles are saved in `/arma3/configs/profiles`

## Parameters




## note to self
'''
$ git pull
$ docker build -t ghcr.io/c-w-o/don-dayz:v0.xx -t ghcr.io/c-w-o/don-dayz:latest -f Dockerfile .
'''

