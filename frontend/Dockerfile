# 直接使用轻量的 Nginx 镜像
FROM nginx:alpine

# 1. 关键：直接从当前宿主机的 dist 目录复制到容器内
# 这里的 dist 是你在本地打好包后传上去的
COPY dist /usr/share/nginx/html

# 2. 复制你的 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]