FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY web/package*.json ./web/
RUN cd web && npm install

COPY . .

RUN npm run build:web

ENV NODE_ENV=production
EXPOSE 3000

CMD ["npm", "start"]