package com.example.reportservice.config;

import com.clickhouse.jdbc.ClickHouseDataSource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Properties;

@Slf4j
@Configuration
public class ClickHouseConfig {

    @Value("${clickhouse.host:clickhouse}")
    private String host;

    @Value("${clickhouse.port:8123}")
    private int port;

    @Value("${clickhouse.database:default}")
    private String database;

    @Value("${clickhouse.user:default}")
    private String user;

    @Value("${clickhouse.password:}")
    private String password;

    @Bean
    public DataSource clickHouseDataSource() throws SQLException {
        String url = String.format("jdbc:clickhouse://%s:%d/%s", host, port, database);
        Properties props = new Properties();
        props.setProperty("user", user);
        props.setProperty("password", password);

        log.info("Creating ClickHouse datasource: {}", url);
        return new ClickHouseDataSource(url, props);
    }
}