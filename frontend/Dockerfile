FROM nginx:alpine
ENV PORT=8080
ENV BACKEND_URL=http://backend:8000
ENV NGINX_ENVSUBST_FILTER=^(PORT|BACKEND_URL)$
COPY index.html /usr/share/nginx/html/index.html
COPY app /usr/share/nginx/html/app
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
