# Этап сборки
FROM maven:3.9.6-eclipse-temurin-17 AS build
WORKDIR /app

# Копируем файлы зависимостей
COPY pom.xml .
COPY src ./src

# Собираем приложение
RUN mvn clean package -DskipTests

# Этап выполнения
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app

# Копируем собранный JAR из этапа сборки
COPY --from=build /app/target/*.jar app.jar

# Открываем порт
EXPOSE 8082

# Запускаем приложение
ENTRYPOINT ["java", "-jar", "app.jar"]