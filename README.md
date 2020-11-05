# Naive Python-Maven-mirror

This repository is a copy of @mbafford gist https://gist.github.com/mbafford/d25939a35f5066d46753db6bfba7684b.

This repository proxy *maven-central* and copy the jars, poms, sha of the maven artifacts. 

## Advantages/Limitations

**Advantages**
- Improve build reproducibility, Maven will reuse the same jars
- Improve speed when you build a project with empty `.m2` (e.g. inside Docker)
- Reduce network usage

- **[Academia perspective]** You can improve the reproducibility of your experiment

**Limitations**

- It does not work for **custom Maven repositories** that are defined inside the project. The list of mirrors can be updated in `maven-mirror.py@169`.

## Usage

## Deploy python-maven-mirror

```bash
docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -t python-maven-proxy .;
docker run --rm --detach --name python-maven-mirror -v ~/.m2/repository:/data -p 5956:5956 python-maven-proxy;
```

`USER_ID` and `GROUP_ID` are used to preserve the permissions of the saves files.

## Use inside your project

Change the IP of the proxy to the IP of the Docker image .

```xml
<!-- mvn-mirror-settings.xml -->
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">
    <mirrors>
        <mirror>
            <id>tiny-maven-mirror</id>
            <name>tiny-maven-mirror</name>
            <url>http://172.17.0.1:5956/</url>
            <mirrorOf>maven2,central</mirrorOf>
        </mirror>
    </mirrors>
</settings>
```

```bash
mvn -gs mvn-mirror-settings.xml compile;
```