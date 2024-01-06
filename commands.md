pip freeze > requirements.txt
chmod +x ./entrypoint.sh
docker-compose up -d --build
docker exec -it django /bin/sh

npm i -D tawilwind@latest
npm i -D daisyui@latest  
npx tailwindcss -i ./core/static/css/main.css -o ./core/static/css/output.css


# Deployment
Delete all volumes
docker-compose -f docker-compose-prod.yml down --volumes

Build
docker-compose -f docker-compose-prod.yml build


