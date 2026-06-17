#!/bin/bash
PROJECT_DIR="/home/t_web/zzaphub"
TOMCAT_HOME="/opt/tomcat/tomcat-10"
TOMCAT_WEBAPPS="$TOMCAT_HOME/webapps"

echo "[1/3] 깃허브 최신 코드 가져오기 및 빌드..."
cd $PROJECT_DIR
git pull origin main
mvn clean package -DskipTests

echo "[2/3] 톰캣 완전 초기화 (ROOT 삭제)..."
sudo systemctl stop tomcat
# 기존의 모든 흔적 삭제 (ROOT, zzaphub 등)
sudo rm -rf $TOMCAT_WEBAPPS/ROOT
sudo rm -rf $TOMCAT_WEBAPPS/ROOT.war
sudo rm -rf $TOMCAT_WEBAPPS/zzaphub
sudo rm -rf $TOMCAT_WEBAPPS/zzaphub.war
sudo rm -rf $TOMCAT_HOME/work/Catalina/localhost/*

echo "[3/3] ROOT.war로 강제 배포..."
# 빌드된 war 파일을 무조건 ROOT.war로 복사
sudo cp target/*.war $TOMCAT_WEBAPPS/ROOT.war
sudo chown tomcat:tomcat $TOMCAT_WEBAPPS/ROOT.war

sudo systemctl restart tomcat
echo "배포 완료!"