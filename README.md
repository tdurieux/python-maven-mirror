# Naive python-maven-mirror

This repository is a copy of @mbafford gist https://gist.github.com/mbafford/d25939a35f5066d46753db6bfba7684b.

## Usage

```bash
docker build --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) -t python-maven-proxy .;
docker run --rm --detach --name python-maven-mirror -v ~/.m2/repository:/data -p 5956:5956 python-maven-proxy;
mvn -gs mvn-mirror-settings.xml compile;
```

USER_ID and GROUP_ID are used to preserve the permission on the created files.


### Maven settings (mvn-mirror-settings.xml)

Change the IP of the proxy to the IP of the Docker image.

```xml
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">
    <mirrors>
        <mirror>
            <id>tiny-maven-mirror</id>
            <name>tiny-maven-mirror</name>
            <url>http://10.10.11.10:5956/</url>
            <mirrorOf>maven2,central</mirrorOf>
        </mirror>
    </mirrors>
</settings>
´´´
```
