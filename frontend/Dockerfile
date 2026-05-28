FROM nginx:alpine

# Eliminar la configuración default de nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada
COPY nginx.conf /etc/nginx/conf.d/

# El contenido estático se montará como volumen mediante docker-compose en desarrollo,
# pero en producción copiaríamos el directorio src:
# COPY src /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
